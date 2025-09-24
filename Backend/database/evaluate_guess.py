def evaluate_guess(guess: str, target: str) -> List[str]:
    feedback = []
    target_letter_count = {}

    # Count target letters
    for ch in target:
        target_letter_count[ch] = target_letter_count.get(ch, 0) + 1

    # First pass: green
    for i in range(5):
        if guess[i] == target[i]:
            feedback.append("green")
            target_letter_count[guess[i]] -= 1
        else:
            feedback.append(None)

    # Second pass: orange / grey
    for i in range(5):
        if feedback[i] is None:
            if guess[i] in target_letter_count and target_letter_count[guess[i]] > 0:
                feedback[i] = "orange"
                target_letter_count[guess[i]] -= 1
            else:
                feedback[i] = "grey"

    return feedback
