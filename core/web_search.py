from ddgs import DDGS


def web_search(query: str, max_results: int = 5) -> list[dict]:
    query = query.strip()

    if not query:
        return []
    results = []
    with DDGS() as ddgs:
        for item in ddgs.text(query, max_results=max_results):
            results.append({
                "title": item.get("title", ""),
                "href": item.get("href", ""),
                "body": item.get("body", ""),
            })

    return results

def format_search_results(results: list[dict]) -> str:
    if not results:
        return "没有找到搜索结果。"
    lines = []
    for index, item in enumerate(results, start=1):
        title = item.get("title", "")
        href = item.get("href", "")
        body = item.get("body", "")

        lines.append(
            f"[{index}] {title}\n"
            f"URL: {href}\n"
            f"摘要: {body}"
        )
    return "\n\n".join(lines)