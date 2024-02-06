import asyncio
import json
import os

import httpx
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils.decorators import classonlymethod
from django.views import View
from textwrap import dedent
from datetime import datetime
from django.core.cache import cache
from .models import Book, Author
from utils.utils import AsyncIter


async def get_term(row: list) -> str:
    return dedent(str(row[0])).replace(" ", "+") + "+" + dedent(str(row[1])).replace(" ", "+")


class BookView(View):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

    async def post(self, *args, **kwargs):
        NBP_API_URL = "http://api.nbp.pl/api/exchangerates/rates/A"
        APPLE_API_ULR = "https://itunes.apple.com/search?term="
        APPLE_PARAM = "&entity=ebook&limit=1"
        DATA_FORMAT = "%Y-%m-%d"

        now = datetime.now()

        body = json.loads(self.request.body.decode("utf-8"))

        search_results = []
        books_batch: [Book] = []
        async with httpx.AsyncClient() as client:
            async for row in AsyncIter(body):
                try:
                    term = await get_term(row)
                except IndexError:
                    error_msg = f'Error for row: "{row}". Please fill data.'
                    return JsonResponse(data=error_msg, status=422, safe=False)

                url_apple = APPLE_API_ULR + term + APPLE_PARAM
                book = await client.get(url_apple)

                if book.status_code == 200:
                    try:
                        book_result = json.loads(book.text)["results"][0]
                        data = datetime.fromisoformat(book_result["releaseDate"]).strftime(DATA_FORMAT)
                        curr: str = book_result["currency"]
                        price = float(book_result["price"])
                        artist: str = book_result["artistName"]
                        title: str = book_result["trackName"]
                    except KeyError:
                        error_msg = f'Error for row: "{row}" in Apple API response.'
                        return JsonResponse(data=error_msg, status=404, safe=False)

                    url_nbp = f"{NBP_API_URL}/{curr}/{data}/"
                    mem = await cache.aget(url_nbp)
                    if mem:
                        rate = mem["rate"]
                        no: str = mem["no"]
                    else:
                        nbp = await client.get(url_nbp)
                        if book.status_code == 200 and nbp.status_code == 200:
                            try:
                                nbp_result: list = json.loads(nbp.text)["rates"][0]
                                rate = float(nbp_result["mid"])
                                no: str = nbp_result["no"]
                                await cache.aset(url_nbp, {"rate": rate, "no": no}, os.environ["CACHE_TTL"])
                            except KeyError:
                                error_msg = f'Error for row: "{row}" in NBP API response.'
                                return JsonResponse(data=error_msg, status=404, safe=False)
                        else:
                            error_msg = f'Error for row: "{row}" in NBP API. Status code: {nbp.status_code}'
                            return JsonResponse(data=error_msg, status=nbp.status_code, safe=False)
                else:
                    error_msg = f'Error for row: "{row}" in Apple API. Status code: {book.status_code}'
                    return JsonResponse(data=error_msg, status=book.status_code, safe=False)

                search_results.append(
                    {
                        "name": artist,
                        "title": title,
                        "curr": curr,
                        "price": price,
                        "date": data,
                        "fromNBP": {
                            "rate": rate,
                            "pricePLN": rate * price,
                            "tableNo": no,
                        },
                    }
                )
                author, created = await Author.objects.aget_or_create(full_name=artist)
                book_instance = Book(
                    author=author,
                    title=title,
                    curr=curr,
                    price=price,
                    publish_date=data,
                    query_date=now,
                    rate=rate,
                    tableNo=no,
                )
                try:
                    book_instance.full_clean()
                    books_batch.append(book_instance)
                except ValidationError as e:
                    error_msg = f'Error for row: "{row}". Error message: {e.message}'
                    return JsonResponse(data=error_msg, status=book.status_code, safe=False)

            await Book.objects.abulk_create(books_batch)

            return JsonResponse(data=search_results, status=200, safe=False)
