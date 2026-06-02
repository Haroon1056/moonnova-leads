from itertools import product


def clean_list(items):
    if not items:
        return []

    cleaned_items = []
    seen = set()

    for item in items:
        if item is None:
            continue

        item = str(item).strip()

        if not item:
            continue

        key = item.lower()

        if key in seen:
            continue

        seen.add(key)
        cleaned_items.append(item)

    return cleaned_items


def generate_queries(keywords, locations):
    keywords = clean_list(keywords)
    locations = clean_list(locations)

    queries = []

    for keyword, location in product(keywords, locations):
        query = f"{keyword} in {location}".strip()

        if query:
            queries.append(query)

    return queries



















# from itertools import product


# def clean_list(items):
#     """
#     Clean keyword/location list and remove empty or duplicate values.
#     """

#     if not items:
#         return []

#     cleaned_items = []
#     seen = set()

#     for item in items:
#         if item is None:
#             continue

#         item = str(item).strip()

#         if not item:
#             continue

#         key = item.lower()

#         if key in seen:
#             continue

#         seen.add(key)
#         cleaned_items.append(item)

#     return cleaned_items


# def generate_queries(keywords, locations):
#     """
#     Creates combinations:

#     keyword × location

#     Example:
#     keywords = ["plumber", "electrician"]
#     locations = ["Austin TX", "Dallas TX"]

#     Output:
#     [
#         "plumber in Austin TX",
#         "plumber in Dallas TX",
#         "electrician in Austin TX",
#         "electrician in Dallas TX"
#     ]
#     """

#     keywords = clean_list(keywords)
#     locations = clean_list(locations)

#     queries = []

#     for keyword, location in product(keywords, locations):
#         query = f"{keyword} in {location}".strip()

#         if query:
#             queries.append(query)

#     return queries