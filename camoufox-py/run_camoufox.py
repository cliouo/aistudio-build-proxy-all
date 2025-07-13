import argparse
import multiprocessing
import os
import yaml

from browser.instance import run_browser_instance
from utils.logger import setup_logging

def main():
    """
    主函数，读取 YAML 配置并为每个实例启动一个独立的浏览器进程。
    """
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    logger = setup_logging(os.path.join(log_dir, 'app.log'))

    logger.info("---------------------Camoufox 实例管理器开始启动---------------------")

    parser = argparse.ArgumentParser(description="通过 YAML 配置文件并发运行多个 Camoufox 实例。")
    parser.add_argument("config_file", help="YAML 配置文件的路径。")
    args = parser.parse_args()

    if not os.path.exists(args.config_file):
        logger.error(f"错误: 配置文件未找到 at {args.config_file}")
        return

    try:
        with open(args.config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.exception(f"读取或解析 YAML 配置文件时出错: {e}")
        return

    global_settings = config.get('global_settings', {})
    instance_profiles = config.get('instances', [])

    if not instance_profiles:
        logger.error("错误: 在配置文件中没有找到 'instances' 列表。")
        return

    processes = []
    for profile in instance_profiles:
        final_config = global_settings.copy()
        final_config.update(profile)

        if 'cookie_file' not in final_config or 'url' not in final_config:
            logger.warning(f"警告: 跳过一个无效的配置项 (缺少 cookie_file 或 url): {profile}")
            continue
            
        process = multiprocessing.Process(target=run_browser_instance, args=(final_config,))
        processes.append(process)
        process.start()

    logger.info(f"已成功启动 {len(processes)} 个浏览器实例。按 Ctrl+C 终止所有实例。")

    try:
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        logger.info("捕获到 Ctrl+C, 正在终止所有子进程...")
        for process in processes:
            process.terminate()
            process.join()
        logger.info("所有进程已终止。")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()