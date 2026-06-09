"""Rule-matching engine — port of transcripcion.cpp."""


def apply_rules(text: str, rules: dict[int, list], use_sv: bool = False) -> str:
    result = []
    pos = 0
    length = len(text)

    while pos < length:
        b = ord(text[pos])
        rule_list = rules.get(b)
        matched = False

        if rule_list:
            for antecedent, consume, consequent in rule_list:
                ant_len = len(antecedent)
                if pos + ant_len <= length and text[pos:pos + ant_len] == antecedent:
                    result.append(consequent)
                    pos += consume
                    matched = True
                    break

        if not matched:
            result.append(text[pos])
            pos += 1

    return "".join(result)
