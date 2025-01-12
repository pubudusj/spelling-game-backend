def lambda_handler(event, context):
    unique_results = []
    seen_words = set()

    for item in event:
        if "word" in item:
            word = item["word"].lower()
            if word not in seen_words:
                item.pop("word", None)
                unique_results.append(item)
                seen_words.add(word)

    return unique_results
