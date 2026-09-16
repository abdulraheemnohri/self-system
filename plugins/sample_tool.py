"""
Sample Plugin for Complete Self System
نمونہ پلگ ان
"""


def execute(args):
    """
    Execute the sample tool
    
    Args:
        args: Dictionary of arguments
        
    Returns:
        Result as string
    """
    name = args.get("name", "world")
    return f"Sample plugin received: {name}"


if __name__ == "__main__":
    print(execute({"name": "test"}))