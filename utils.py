from selene import be, browser
from selene.core.entity import Element


def send_keys_one_by_one(element: Element, keys: str):
    for key in keys:
        element.send_keys(key)


def wait_for_loading():
    # print("Waiting for loading...", end="\r")
    try:
        element = browser.element("div[class$='x-mask-loading']")
        element.wait.for_(be.existing)
        element.wait.for_(be.not_.existing)
    # except TimeoutException:
    #     pass
    except Exception:
        pass
    # print("Loading completed.    ")
