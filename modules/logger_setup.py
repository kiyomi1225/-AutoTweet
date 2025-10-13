# modules/logger_setup.py - ログ設定
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import sys

def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """
    ログ設定をセットアップ
    
    Args:
        name: ロガー名
        log_file: ログファイルパス
        level: ログレベル
        
    Returns:
        logging.Logger: 設定済みロガー
    """
    # ログディレクトリを作成
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # ロガーを取得（既存のハンドラーをクリア）
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(level)
    
    # フォーマッターを定義
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # ファイルハンドラー（日次ローテーション）
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # 30日分保持
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # コンソール用の簡略フォーマッター
    console_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 重複ログ防止
    logger.propagate = False
    
    return logger

def setup_module_logger(module_name: str, main_logger_name: str = "TwitterAutomation") -> logging.Logger:
    """
    モジュール専用ロガーをセットアップ
    
    Args:
        module_name: モジュール名
        main_logger_name: メインロガー名
        
    Returns:
        logging.Logger: モジュール専用ロガー
    """
    logger_name = f"{main_logger_name}.{module_name}"
    logger = logging.getLogger(logger_name)
    
    # 親ロガーが存在しない場合は基本設定
    if not logger.parent.handlers:
        setup_logger(main_logger_name, f"logs/{main_logger_name.lower()}.log")
    
    return logger

def log_function_call(func):
    """
    関数呼び出しをログ出力するデコレータ
    
    Args:
        func: デコレート対象の関数
        
    Returns:
        function: ラップされた関数
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger("TwitterAutomation.FunctionCall")
        logger.debug(f"関数呼び出し: {func.__name__} - args: {args}, kwargs: {kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"関数完了: {func.__name__} - 結果: {type(result)}")
            return result
        except Exception as e:
            logger.error(f"関数エラー: {func.__name__} - {str(e)}")
            raise
    
    return wrapper

def setup_error_logger() -> logging.Logger:
    """
    エラー専用ロガーをセットアップ
    
    Returns:
        logging.Logger: エラー専用ロガー
    """
    error_logger = setup_logger(
        "TwitterAutomation.Error", 
        "logs/error.log", 
        logging.ERROR
    )
    return error_logger

def log_system_info():
    """
    システム情報をログ出力
    """
    logger = logging.getLogger("TwitterAutomation")
    
    import platform
    import psutil
    
    logger.info("=== システム情報 ===")
    logger.info(f"OS: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"CPU: {psutil.cpu_count()} cores")
    logger.info(f"メモリ: {psutil.virtual_memory().total // (1024**3)} GB")
    logger.info(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("==================")

# 使用例とテスト関数
def test_logger():
    """
    ロガーのテスト関数
    """
    # メインロガーのセットアップ
    main_logger = setup_logger("TestLogger", "logs/test.log", logging.DEBUG)
    
    # 各レベルのテスト
    main_logger.debug("デバッグメッセージのテスト")
    main_logger.info("情報メッセージのテスト")
    main_logger.warning("警告メッセージのテスト")
    main_logger.error("エラーメッセージのテスト")
    
    # モジュールロガーのテスト
    module_logger = setup_module_logger("TestModule", "TestLogger")
    module_logger.info("モジュールロガーのテスト")
    
    # エラーロガーのテスト
    error_logger = setup_error_logger()
    error_logger.error("エラー専用ロガーのテスト")
    
    print("ログテスト完了。logs/ディレクトリを確認してください。")

if __name__ == "__main__":
    test_logger()