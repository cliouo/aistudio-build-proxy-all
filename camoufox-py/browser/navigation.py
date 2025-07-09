import time
import os
from playwright.sync_api import Page, expect

def handle_untrusted_dialog(page: Page, logger=None):
    """
    检查并处理 "Last modified by..." 的弹窗。
    如果弹窗出现，则点击 "OK" 按钮。
    """
    ok_button_locator = page.get_by_role("button", name="OK")

    try:
        if ok_button_locator.is_visible(timeout=10000): # 等待最多10秒
            logger.info(f"检测到弹窗，正在点击 'OK' 按钮...")

            ok_button_locator.click(force=True)
            logger.info(f"'OK' 按钮已点击。")
            expect(ok_button_locator).to_be_hidden(timeout=1000)
            logger.info(f"弹窗已确认关闭。")
        else:
            logger.info(f"在10秒内未检测到弹窗，继续执行...")
    except Exception as e:
        logger.info(f"检查弹窗时发生意外：{e}，将继续执行...")

def handle_build_dialog(page: Page, logger=None):
    """
    检查并处理 It's time to build 弹窗的关闭按钮。
    如果弹窗出现，则点击关闭按钮。
    """
    # 使用更精确的选择器定位关闭按钮
    close_button_locator = page.locator("#warm-welcome-dialog-test-id > div > div > app-warm-welcome > mat-dialog-actions.mat-mdc-dialog-actions.mdc-dialog__actions.mat-mdc-dialog-actions-align-end > button > span.mat-mdc-button-persistent-ripple.mdc-icon-button__ripple")

    try:
        if close_button_locator.is_visible(timeout=10000): # 等待最多10秒
            logger.info(f"检测到 It's time to build 弹窗，正在点击关闭按钮...")

            close_button_locator.click(force=True)
            logger.info(f"It's time to build 弹窗关闭按钮已点击。")
            # 等待弹窗消失
            page.wait_for_timeout(1000)
            logger.info(f"It's time to build 弹窗已确认关闭。")
        else:
            logger.info(f"在10秒内未检测到 It's time to build 弹窗，继续执行...")
    except Exception as e:
        logger.info(f"检查 It's time to build 弹窗时发生意外：{e}，将继续执行...")

def handle_successful_navigation(page: Page, logger, cookie_file_config):
    """
    在成功导航到目标页面后，执行后续操作（处理弹窗、截图、保持运行）。
    """
    logger.info("已成功到达目标页面。")
    page.click('body') # 给予页面焦点

    # 检查并处理 "Last modified by..." 的弹窗
    handle_untrusted_dialog(page, logger=logger)

    # 检查并处理 It's time to build 弹窗
    handle_build_dialog(page, logger=logger)

    # 等待页面加载和渲染后截图
    logger.info("等待15秒以便页面完全渲染...")
    time.sleep(15)
    
    screenshot_dir = 'logs'
    screenshot_filename = os.path.join(screenshot_dir, f"screenshot_{cookie_file_config}_{int(time.time())}.png")
    try:
        page.screenshot(path=screenshot_filename, full_page=True)
        logger.info(f"已截屏到: {screenshot_filename}")
    except Exception as e:
        logger.error(f"截屏时出错: {e}")
        
    logger.info("实例将保持运行状态。每10秒点击一次页面以保持活动。")
    while True:
        try:
            page.click('body')
            time.sleep(10)
        except Exception as e:
            logger.error(f"在保持活动循环中出错: {e}")
            break # 如果页面关闭或出错，则退出循环
