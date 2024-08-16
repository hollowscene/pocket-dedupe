"""Pocket dedupe script.

Thanks go out to Matt Oswalt for their blog post
https://oswalt.dev/2015/01/remove-duplicates-from-pocket-list/ which includes a
link to the original code that this script was forked from
https://gist.github.com/Mierdin/0996952ba02d87175f3b.

Thanks also go out to all of the contributors to the Python wrapper of the
Pocket API https://github.com/tapanpandita/pocket.

How to run:
1.  Create a Pocket consumer key https://getpocket.com/developer/apps/.
2.  Ensure required packages are installed in your environment.
    `pip install -r requirements.txt`
3.  Run pocket_dedupe from the command line.
    `python pocket_dedupe.py`
4.  Follow the instructions as they appear in the command line.
"""

import webbrowser

from pocket import Pocket

STRIP_PARAMETERS = [
    "?utm", # Urchin Tracking Module parameters (https://en.wikipedia.org/wiki/UTM_parameters)
    "&utm",
    "?CMP", # Generic campaign parameters (The Guardian)
    "&CMP",
]


def authenticate(consumer_key: str, redirect_uri: str) -> str:
    """Open authentication webpage to authorise Pocket API access.

    Args:
        consumer_key: Pocket API consumer key retrieved from
          https://getpocket.com/developer/apps/.
        redirect_uri: Webpage to redirect user to after authentication.

    Returns:
        A Pocket API request token.
    """

    request_token = Pocket.get_request_token(
        consumer_key=consumer_key,
        redirect_uri=redirect_uri,
    )
    auth_url = Pocket.get_auth_url(
        code=request_token,
        redirect_uri=redirect_uri,
    )

    print("Opening a browser tab to authenticate with Pocket.")
    webbrowser.open_new_tab(auth_url)

    input("After you have authenticated in the browser, press Enter...")

    return request_token


def get_pocket_instance(consumer_key: str = None, redirect_uri: str = "https://google.com/") -> Pocket:
    """Create and authenticate Pocket API connection.

    Args:
        consumer_key: Pocket API consumer key retrieved from
          https://getpocket.com/developer/apps/.
        redirect_uri: Webpage to redirect user to after authentication.

    Returns:
        A Pocket API connection.
    """

    if consumer_key is None:
        consumer_key = input("Enter your Pocket consumer key: ").strip()

    request_token = authenticate(consumer_key, redirect_uri)

    access_token = Pocket.get_access_token(
        consumer_key=consumer_key,
        code=request_token,
    )

    return Pocket(consumer_key, access_token)


def strip_url(url: str, char: str) -> str:
    """Strip all text after given parameter from URL.

    Args:
        url: Pocket article URL.
        char: Target parameter to strip from url.

    Returns:
        The pocket article URL with text after the target parameter stripped.
    """
    try:
        return url[:url.index(char)]
    except ValueError:
        return url


def queue_dedupe_actions(pocket_instance: Pocket):
    """Identifies duplicate articles and chains modify methods to Pocket API.

    Duplicate Pocket articles generally arise from site trackers such as the
    UTM (Urchin Tracking Modules) parameters. See
    https://oswalt.dev/2015/01/remove-duplicates-from-pocket-list/.

    This function will create a bulk send request containing actions to delete
    duplicate articles, and strip trackers from all other articles.

    NB: Stripping trackers from articles is unimplemented as the Pocket API
    does not provide any way to retain an item's original metadata, most
    importantly time_added and time_read).

    Args:
        pocket_instance: Pocket API connection.
    """

    response_output, response_header = pocket_instance.get(state="all", sort="oldest")

    # with open("response_output.json", "w") as out:
    #     out.write(json.dumps(dict(response_output)))

    # with open("response_header.json", "w") as out:
    #     out.write(json.dumps(dict(response_header)))

    items_list = response_output["list"]

    print(f"Found {len(items_list)} articles.")

    article_cache = []

    for item in items_list:

        article_id = items_list[item]["item_id"]
        article_url = items_list[item]["given_url"]
        original_article_url = article_url

        for param in STRIP_PARAMETERS:
            if param in article_url:
                article_url = strip_url(article_url, param)

        # Article is already in Pocket.
        # TODO: Retain details from the oldest item, except for favourite and archive status.
        if article_url in article_cache:
            print(f"Duplicate article found: {original_article_url}")
            PocketInstance.delete(article_id)  # Queue up deletion of article
            continue

        # Article has not been seen yet.
        # Check if the url has parameters that were stripped.
        # TODO: Retain parameters from the original item when adding it again. Unfortunately the Pocket API does not allow for this.
        if article_url != original_article_url:
            print(f"Article with trackers found: {original_article_url}")

        article_cache.append(article_url)


# %%

if __name__ == "__main__":

    PocketInstance = get_pocket_instance()
    queue_dedupe_actions(PocketInstance)

    user_input = input("Now's the time to review the changes that will be made. If you are happy to send this to the Pocket API, type in 'y' and press Enter: ").strip()

    if user_input == "y":
        response = PocketInstance.commit()
        print(f"Request sent. Response: {response}")
    else:
        print(f"Received input '{user_input}'. Modify request has not been sent.")

    print("The script has finished running.")
