from time import sleep

from selene import be, browser
from selene.core.entity import Element


def send_keys_one_by_one(
    element: Element, keys: str, sleep_time: float = 0.01
):
    for key in keys:
        element.send_keys(key)
        sleep(sleep_time)


def wait_for_loading():
    # print("Waiting for loading...", end="\r")
    try:
        element = browser.element("div[class$='x-mask-loading']")
        element.wait.for_(be.present)
        element.wait.for_(be.not_.present)
    # except TimeoutException:
    #     pass
    except Exception:
        pass
    # print("Loading completed.    ")
