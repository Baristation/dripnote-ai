def to_instruction_text(record: dict[str, str]) -> str:
    instruction = record.get("instruction", "")
    input_text = record.get("input", "")
    output_text = record.get("output", "")
    return f"Instruction: {instruction}\nInput: {input_text}\nResponse: {output_text}"
