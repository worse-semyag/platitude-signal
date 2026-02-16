class msg_fmt:
    BOLD_START = "\033[1m"
    END = "\033[0m"
    UNDERLINE = "\033[4m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


if __name__ == "__main__":
    print(
        "This text is not bold | |"
        + msg_fmt.BOLD_START
        + msg_fmt.UNDERLINE
        + msg_fmt.PURPLE
        + "This text is bold"
        + msg_fmt.END
    )
