# from config.logging_cfg import LoggingConfig
# from logging.handlers import RotatingFileHandler
# import sys
# import logging

# from pathlib import Path
# sys.path.append(str(Path(__file__).parent))


# class Logger:
#     def __init__(self, name="", log_level=logging.INFO, log_file=None) -> None:
#         self.log = logging.getLogger(name)
#         self.get_logger(log_level, log_file)

#     def get_logger(self, log_level, log_file):
#         self.log.setLevel(log_level)
#         self._init_formatter()

#         if log_file is not None:
#             self._add_file_handler(LoggingConfig.LOG_DIR / log_file)
#         else:
#             self._add_stream_handler()

#     def _init_formatter(self):
#         self.formatter = logging.Formatter(
#             "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#         )

#     def _add_stream_handler(self):
#         stream_handler = logging.StreamHandler(sys.stdout)
#         stream_handler.setFormatter(self.formatter)
#         self.log.addHandler(stream_handler)

#     def _add_file_handler(self, log_file):
#         file_handler = RotatingFileHandler(
#             log_file, maxBytes=10000, backupCount=10)
#         file_handler.setFormatter(self.formatter)
#         self.log.addHandler(file_handler)

#     def log_model(self, predictor_name):
#         self.log.info(f"Predictor name: {predictor_name}")

#     def log_response(self, pred_probs, pred_class_ids):
#         self.log.info(
#             f"Predicted Prob: {pred_probs} - Predicted Class: {pred_class_ids}")
