import logging

basic_formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    style= "%",
    datefmt="%Y-%m-%d %H:%M",
)
#__________________________________________

# Warning Events to File:
app_warning_file_handler = logging.FileHandler(
    filename="app_warning.log",
    encoding="utf-8",
    mode="a"
)
app_warning_file_handler.setLevel(logging.WARNING)
app_warning_file_handler.setFormatter(basic_formatter)

# Regular Events to File:
app_regular_file_handler = logging.FileHandler(
    filename="app_regular.log",
    encoding="utf-8",
    mode="a"
)
app_regular_file_handler.setLevel(logging.INFO)
app_regular_file_handler.setFormatter(basic_formatter)