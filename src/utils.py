def format_number(num):
    """
    Formats a large number into a short string with suffixes.
    """
    if num < 1000:
        return str(int(num))
        
    for unit in ['K', 'M', 'B', 'T', 'Q']:
        num /= 1000.0
        if num < 999.95:
            formatted = f"{num:.1f}{unit}"
            return formatted.replace(".0", "")
            
    return f"TOO BIG"