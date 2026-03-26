# src/interpretability/clinical_translator.py
import numpy as np

class ClinicalTranslator:
    def __init__(self, tm_model, biomarker_names, max_bits=4):
        self.tm = tm_model
        self.bm_names = biomarker_names
        self.max_bits = max_bits
        self.half_features = tm_model.number_of_features // 2

    def _decode_clause(self, class_idx, clause_idx):
        """
        Translates a single mathematical clause into medical language.
        """
        conditions = []
        for k in range(self.tm.number_of_features):
            if self.tm.ta_action(class_idx, clause_idx, k) == 1:
                is_negation = k >= self.half_features
                actual_k = k - self.half_features if is_negation else k
                
                bm_index = actual_k // self.max_bits
                quartile = (actual_k % self.max_bits) + 1
                bm_name = self.bm_names[bm_index]
                
                if is_negation:
                    conditions.append(f"[{bm_name} NOT in Q{quartile}]")
                else:
                    conditions.append(f"[{bm_name} in Q{quartile}]")
        return " AND ".join(conditions)

    def _evaluate_coverage(self, class_idx, clause_idx, X_bool, Y_true):
        """
        Calculates how many real patients satisfy this specific mathematical rule.
        """
        satisfies_rule = np.ones(X_bool.shape[0], dtype=bool)

        for k in range(self.tm.number_of_features):
            if self.tm.ta_action(class_idx, clause_idx, k) == 1:
                is_negation = k >= self.half_features
                actual_k = k - self.half_features if is_negation else k

                # X_bool has the original features. We check 0 for negations, 1 for affirmations.
                if is_negation:
                    satisfies_rule = satisfies_rule & (X_bool[:, actual_k] == 0)
                else:
                    satisfies_rule = satisfies_rule & (X_bool[:, actual_k] == 1)

        total_satisfied = np.sum(satisfies_rule)
        if total_satisfied == 0:
            return 0.0, 0.0
            
        target_mask = (Y_true == class_idx)
        true_positives = np.sum(satisfies_rule & target_mask)

        # Coverage: % of target patients found. Precision: Accuracy of the rule.
        coverage = true_positives / np.sum(target_mask)
        precision = true_positives / total_satisfied

        return coverage, precision

    def get_clinical_profiles(self, X_data, Y_data, max_rules_per_class=4):
        """
        Extracts rules and ranks them by their Coverage (Support) on the provided dataset.
        """
        report = []
        report.append("================ CLINICAL PROFILE RANKING ================\n")
        
        for i in range(self.tm.number_of_classes):
            status = 'INFECTED (Peritonitis)' if i == 1 else 'HEALTHY (Homeostasis)'
            report.append(f"--- DIAGNOSTIC RULES FOR {status} ---")
            
            valid_rules = []
            
            # Extract and evaluate all positive clauses
            for j in range(0, self.tm.number_of_clauses, 2):
                rule_text = self._decode_clause(i, j)
                if rule_text:
                    coverage, precision = self._evaluate_coverage(i, j, X_data, Y_data)
                    # Only keep rules that actually cover at least some patients
                    if coverage > 0:
                        valid_rules.append({
                            'text': rule_text,
                            'coverage': coverage,
                            'precision': precision
                        })
            
            # Sort rules by highest coverage (Support)
            sorted_rules = sorted(valid_rules, key=lambda x: x['coverage'], reverse=True)
            
            # Print the top N rules
            for rank, rule in enumerate(sorted_rules[:max_rules_per_class]):
                report.append(
                    f"  Rank #{rank + 1} (Coverage: {rule['coverage']:.1%} | Precision: {rule['precision']:.1%})\n"
                    f"  IF ( {rule['text']} )\n"
                )
            report.append("\n")
            
        return "\n".join(report)