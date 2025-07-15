import re

def parse_response(response_text: str, object_str: str) -> tuple[str, bool]:
    """
    Parse VLM response for coordinates from a table, rescale to original resolution (640x480).
    Returns formatted table string and recognized flag.
    """
    print(f"Parsing response: {response_text}")
    # Find all table rows (skip header and separator)
    lines = [line.strip() for line in response_text.strip().split('\n')]
    data_rows = []
    for line in lines:
        if re.match(r'^\|\s*\d+', line):  # Row starts with | and a number
            data_rows.append(line)
    if not data_rows:
        return "0 | 0 | 0", False

    coordinates = []
    for row in data_rows:
        cells = [cell.strip() for cell in row.strip('|').split('|')]
        print(f"Raw cells from row '{row}': {cells}")  # Debug the extracted cells
        if len(cells) >= 3:
            try:
                h = int(cells[0])
                v = int(cells[1])
                id_num = cells[2] if cells[2].isdigit() else "0"
                # Rescale coordinates to original resolution (640x480)
                original_width, original_height = 640, 480
                new_width, new_height = 256, 192
                scaled_h = int(h * (original_width / new_width))
                scaled_v = int(v * (original_height / new_height))
                coordinates.append((scaled_h, scaled_v, id_num))
                print(f"Extracted and scaled: H={scaled_h}, V={scaled_v}, ID={id_num}")
            except Exception as e:
                print(f"Skipping invalid row due to {e}: {row}")

    if not coordinates:
        return "0 | 0 | 0", False

    recognized = True
    if len(coordinates) == 1:
        h, v, id_num = coordinates[0]
        return f"{h} | {v} | {id_num}", recognized
    else:
        coord_str = "; ".join([f"{h} | {v} | {id_num}" for h, v, id_num in coordinates])
        return coord_str, recognized

def generate_response(object_str: str, recognized: bool, coord_str: str) -> str:
    """
    Generate textual response based on recognition, including a concise table.
    """
    if recognized:
        return f"{object_str} is recognized, let me fetch it to you\n\nRaw Text Output:\n{coord_str}"
    else:
        return "sorry, I cannot locate it\n\nRaw Text Output:\n0 | 0 | 0"

# Example usage with the raw API response you provided
if __name__ == "__main__":
    # Sample response text (your actual response)
    sample_response = """| H | V | ID |
|---|---|---|
| 144 | 96 | 1 |"""
    
    object_str = "coke"  # Example object
    coord_str, recognized = parse_response(sample_response, object_str)
    resp_text = generate_response(object_str, recognized, coord_str)
    print(resp_text)