from __future__ import annotations
from collections import deque, defaultdict
from datetime import datetime, timezone
from typing import Dict, Any, Deque, Set
import uuid
import hashlib

try:
    from config import CoreConfig
    from logging_config import setup_logging
    from models import Concept, Rule, SystemMetrics
    from similarity import get_similarity
    from decay import exponential_decay_factor
    from persistence import JsonCheckpointStore
except ImportError:
    from universal_core.config import CoreConfig
    from universal_core.logging_config import setup_logging
    from universal_core.models import Concept, Rule, SystemMetrics
    from universal_core.similarity import get_similarity
    from universal_core.decay import exponential_decay_factor
    from universal_core.persistence import JsonCheckpointStore

logger = setup_logging("UniversalMind")

class UniversalCognitiveCore:
    def __init__(self, mind_id: str, config: CoreConfig | None = None):
        self.mind_id = mind_id
        self.config = config or CoreConfig()
        self.iteration = 0
        self.start_time = datetime.now(timezone.utc).timestamp()

        self.concepts: Dict[str, Concept] = {}
        self.rules: Dict[str, Rule] = {}
        self.short_term_memory: Deque[Dict[str, Any]] = deque(
            maxlen=self.config.max_memory_size
        )
        self.cross_domain_mappings: Dict[str, Set[str]] = defaultdict(set)
        self.metrics = SystemMetrics()
        self._checkpoint_store = JsonCheckpointStore(self.config.checkpoint_dir / f"{mind_id}.json")
        self._last_decay_time = self.start_time
        self._similarity_fn = get_similarity(self.config.similarity_method)

        logger.info("Universal Mind '%s' initialized", mind_id)

    def _normalize_observation(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        current_time = datetime.now(timezone.utc).timestamp()
        ts = obs.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts = dt.timestamp()
            except Exception:
                ts = current_time
        elif not isinstance(ts, (int, float)):
            ts = current_time
        obs["timestamp"] = float(ts)
        return obs

    def _create_feature_vector(self, obs: Dict[str, Any]) -> Dict[str, float]:
        features: Dict[str, float] = {}
        for k, v in obs.items():
            if k in ("timestamp", "symbol", "domain"):
                continue
            if isinstance(v, (int, float)):
                features[k] = float(v)
        return features

    def _apply_concept_decay(self, current_time: float) -> None:
        to_remove = []
        for cid, concept in self.concepts.items():
            factor = exponential_decay_factor(
                current_time, concept.last_seen, self.config.concept_half_life_hours
            )
            concept.confidence *= factor
            if concept.confidence < self.config.min_confidence_threshold:
                to_remove.append(cid)
        for cid in to_remove:
            del self.concepts[cid]
            self.metrics.concepts_decayed += 1
        if to_remove:
            logger.info("Decayed %d concepts", len(to_remove))

    def _find_best_concept(
        self, domain: str, feature_vector: Dict[str, float]
    ) -> Concept | None:
        best: Concept | None = None
        best_sim = 0.0
        for concept in self.concepts.values():
            if concept.domain != domain:
                continue
            if not concept.examples:
                continue
            recent = concept.examples[-1]
            recent_vec = self._create_feature_vector(recent)
            sim = self._similarity_fn(feature_vector, recent_vec)
            if sim > best_sim:
                best_sim = sim
                best = concept
        if best and best_sim >= self.config.concept_similarity_threshold:
            return best
        return None

    def _form_concept(
        self, obs: Dict[str, Any], domain: str, current_time: float
    ) -> str:
        fv = self._create_feature_vector(obs)
        if not fv:
            return ""

        existing = self._find_best_concept(domain, fv)
        if existing:
            existing.examples.append(obs)
            existing.update_temporal_metrics(current_time)
            existing.confidence = min(1.0, existing.confidence + 0.05)
            logger.debug(
                "Strengthened concept %s (confidence=%.3f)",
                existing.id,
                existing.confidence,
            )
            return existing.id

        cid = f"concept_{uuid.uuid4().hex}"
        concept = Concept(
            id=cid,
            domain=domain,
            signature=fv,
            examples=deque([obs], maxlen=100),
            first_seen=current_time,
            last_seen=current_time,
        )
        concept.update_temporal_metrics(current_time)
        concept.confidence = 0.1
        self.concepts[cid] = concept
        self.metrics.concepts_formed += 1
        logger.info("New concept %s in domain '%s'", cid, domain)
        return cid

    def _hash_rule(self, rule: Rule) -> str:
        content = f"{rule.antecedent}→{rule.consequent}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _infer_rules(self, obs: Dict[str, Any], current_time: float) -> list[Rule]:
        keys = [k for k in obs.keys() if k not in ("timestamp", "domain", "symbol")]
        rules: list[Rule] = []
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                v1, v2 = obs.get(k1), obs.get(k2)
                if not isinstance(v1, (int, float)) or not isinstance(v2, (int, float)):
                    continue

                if v2 > 0 and v1 > 0.7 * v2:
                    rules.append(
                        Rule(
                            antecedent=f"{k1}_high",
                            consequent=f"{k2}_elevated",
                            confidence=0.7,
                            created_at=current_time,
                            last_seen=current_time,
                        )
                    )

                denom = max(abs(v1), abs(v2), 1.0)
                if abs(v1 - v2) / denom < 0.1:
                    rules.append(
                        Rule(
                            antecedent=f"{k1}_similar",
                            consequent=f"{k2}_similar",
                            confidence=0.8,
                            created_at=current_time,
                            last_seen=current_time,
                        )
                    )
        return rules[: self.config.max_rules_per_observation]

    def _process_rules(self, new_rules: list[Rule], current_time: float) -> None:
        for rule in new_rules:
            rid = self._hash_rule(rule)
            existing = self.rules.get(rid)
            if existing:
                existing.support += 1
                existing.update_temporal(current_time)
                existing.confidence = min(1.0, existing.confidence + 0.02)
            else:
                self.rules[rid] = rule
                self.metrics.rules_learned += 1

    def _get_active_domains(self) -> set[str]:
        return {c.domain for c in self.concepts.values()}

    def _attempt_cross_domain_transfer(self, current_domain: str) -> None:
        domains = self._get_active_domains()
        for other in domains:
            if other == current_domain:
                continue
            if other not in self.cross_domain_mappings[current_domain]:
                self.cross_domain_mappings[current_domain].add(other)
                self.metrics.transfers_made += 1
                logger.info("Transfer: %s → %s", current_domain, other)

    def _generate_autonomous_goals(self, obs: Dict[str, Any]) -> None:
        self.metrics.goals_generated += 1
        logger.debug("Goal: analyze covariation in %s", list(obs.keys())[:3])

    def _checkpoint_if_needed(self) -> None:
        if self.iteration % self.config.checkpoint_interval == 0:
            self._checkpoint_store.save(
                self.concepts, self.rules, self.metrics, self.iteration
            )

    def ingest(self, observation: Dict[str, Any], domain: str) -> Dict[str, Any]:
        current_time = datetime.now(timezone.utc).timestamp()
        self.iteration += 1
        self.metrics.total_observations += 1
        self.metrics.last_observation_time = current_time
        self.metrics.uptime_seconds = current_time - self.metrics.start_time

        try:
            observation["domain"] = domain
            observation = self._normalize_observation(observation)
            self.short_term_memory.append(observation)

            if current_time - self._last_decay_time > self.config.decay_check_interval:
                self._apply_concept_decay(current_time)
                self._last_decay_time = current_time

            concept_id = self._form_concept(observation, domain, current_time)
        except Exception as e:
            self.metrics.errors += 1
            logger.exception("Error in concept formation")
            concept_id = ""

        try:
            new_rules = self._infer_rules(observation, current_time)
            self._process_rules(new_rules, current_time)
        except Exception:
            self.metrics.errors += 1
            logger.exception("Error in rule inference")
            new_rules = []

        try:
            if len(self._get_active_domains()) > 1:
                self._attempt_cross_domain_transfer(domain)
        except Exception:
            self.metrics.errors += 1
            logger.exception("Error in cross-domain transfer")

        if self.iteration % self.config.goal_generation_interval == 0:
            self._generate_autonomous_goals(observation)

        self._checkpoint_if_needed()

        return {
            "success": True,
            "iteration": self.iteration,
            "concept_id": concept_id,
            "new_rules": len(new_rules),
            "concept_count": len(self.concepts),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
