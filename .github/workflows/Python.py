import os
import io
import zipfile
import asyncio
import aiohttp
from pathlib import Path


API = "https://sansansekai.miraheze.org/w/api.php"

OUTPUT = Path("sansansekai_images.zip")

CONCURRENCY = 24

RETRIES = 5

TIMEOUT = aiohttp.ClientTimeout(
    total=180,
    connect=30,
    sock_read=150,
)


def safe_name(name: str) -> str:
    if name.startswith("ファイル:"):
        name = name[5:]

    invalid = '<>:"/\\|?*\x00-\x1f'

    name = "".join(
        "_" if c in invalid else c
        for c in name
    )

    name = name.strip().rstrip(". ")

    return name or "unnamed"


async def get_image_list(session):
    images = []

    params = {
        "action": "query",
        "generator": "allimages",
        "gailimit": "max",
        "prop": "imageinfo",
        "iiprop": "url",
        "format": "json",
        "formatversion": "2",
    }

    page = 0

    while True:
        page += 1

        print(
            f"[API] ページ {page} / "
            f"現在 {len(images)} 件"
        )

        async with session.get(
            API,
            params=params,
        ) as response:

            response.raise_for_status()

            data = await response.json()

        for item in data.get(
            "query",
            {}
        ).get(
            "pages",
            []
        ):

            info = (
                item.get("imageinfo") or []
            )

            if not info:
                continue

            url = info[0].get("url")

            if not url:
                continue

            images.append(
                {
                    "name": safe_name(
                        item.get(
                            "title",
                            ""
                        )
                    ),
                    "url": url,
                }
            )

        continuation = data.get(
            "continue"
        )

        if not continuation:
            break

        params.update(
            continuation
        )

    used = set()

    for index, image in enumerate(images):
        original = image["name"]
        name = original

        if name in used:
            stem, ext = os.path.splitext(
                original
            )

            counter = 2

            while name in used:
                name = (
                    f"{stem}_{counter}"
                    f"{ext}"
                )
                counter += 1

        used.add(name)

        image["name"] = name

    return images


async def download_one(
    session,
    semaphore,
    image,
    index,
    total,
):
    async with semaphore:

        for attempt in range(
            1,
            RETRIES + 1
        ):

            try:

                async with session.get(
                    image["url"],
                    headers={
                        "User-Agent":
                        "SansanSekaiWikiImageDownloader/1.0"
                    },
                ) as response:

                    if response.status in (
                        429,
                        502,
                        503,
                    ):

                        raise aiohttp.ClientResponseError(
                            response.request_info,
                            response.history,
                            status=response.status,
                        )

                    response.raise_for_status()

                    data = await response.read()

                if not data:
                    raise RuntimeError(
                        "0 byte"
                    )

                print(
                    f"[{index}/{total}] "
                    f"OK "
                    f"{image['name']} "
                    f"({len(data):,} bytes)"
                )

                return {
                    "name":
                        image["name"],
                    "data":
                        data,
                    "error":
                        None,
                }

            except Exception as error:

                print(
                    f"[{index}/{total}] "
                    f"retry {attempt}/"
                    f"{RETRIES}: "
                    f"{image['name']} "
                    f"{error}"
                )

                if attempt < RETRIES:

                    await asyncio.sleep(
                        min(
                            attempt * 2,
                            10
                        )
                    )

        return {
            "name":
                image["name"],
            "data":
                None,
            "error":
                "download failed",
        }


async def download_all(
    images,
):
    connector = aiohttp.TCPConnector(
        limit=CONCURRENCY,
        limit_per_host=CONCURRENCY,
        ttl_dns_cache=300,
    )

    semaphore = asyncio.Semaphore(
        CONCURRENCY
    )

    async with aiohttp.ClientSession(
        timeout=TIMEOUT,
        connector=connector,
    ) as session:

        tasks = [
            download_one(
                session,
                semaphore,
                image,
                index + 1,
                len(images),
            )
            for index, image
            in enumerate(images)
        ]

        return await asyncio.gather(
            *tasks
        )


def make_zip(results):

    success = 0
    failed = 0

    print()
    print(
        "[ZIP] 全画像のダウンロード完了。"
    )
    print(
        "[ZIP] ZIP生成を開始します。"
    )

    with zipfile.ZipFile(
        OUTPUT,
        "w",
        compression=zipfile.ZIP_STORED,
        allowZip64=True,
    ) as archive:

        for result in results:

            if result["data"] is None:

                failed += 1

                print(
                    "[ZIP] SKIP "
                    + result["name"]
                )

                continue

            archive.writestr(
                result["name"],
                result["data"],
            )

            success += 1

    print()
    print(
        "[ZIP] 完了"
    )

    print(
        f"[ZIP] 成功: {success}"
    )

    print(
        f"[ZIP] 失敗: {failed}"
    )

    print(
        f"[ZIP] サイズ: "
        f"{OUTPUT.stat().st_size:,} bytes"
    )


async def main():

    print(
        "=== 燦々世界Wiki画像一括取得 ==="
    )

    print(
        f"並列数: {CONCURRENCY}"
    )

    async with aiohttp.ClientSession(
        timeout=TIMEOUT,
    ) as session:

        images = await get_image_list(
            session
        )

    print()
    print(
        f"画像総数: {len(images)}"
    )

    if not images:
        raise RuntimeError(
            "画像がありません。"
        )

    print()
    print(
        "全画像のダウンロードを開始します。"
    )

    results = await download_all(
        images
    )

    # ここまで来るまでZIPは作らない
    make_zip(results)


if __name__ == "__main__":
    asyncio.run(main())
