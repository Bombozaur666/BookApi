import asyncio
import json
import httpx
from django.http import JsonResponse
from django.utils.decorators import classonlymethod
from django.views import View
from textwrap import dedent
from datetime import datetime


def get_term(row: list) -> str:
    return dedent(str(row[0])).replace(" ", "+") + "+" + dedent(str(row[1])).replace(" ", "+")


class Book(View):
    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super().as_view(**initkwargs)
        view._is_coroutine = asyncio.coroutines._is_coroutine
        return view

    async def post(self, *args, **kwargs):
        NBP_API_URL = "http://api.nbp.pl/api/exchangerates/rates/A"
        APPLE_API_ULR = "https://itunes.apple.com/search?term="
        APPLE_PARAM = "&entity=ebook&limit=1"
        date_format = "%Y-%m-%d"

        body = json.loads(self.request.body.decode("utf-8"))

        search_results = []
        async with httpx.AsyncClient() as client:
            for row in body:
                try:
                    term = get_term(row)
                except IndexError:
                    error_msg = f'Error for row: "{row}". Please fill data.'
                    return JsonResponse(data=error_msg, status=422, safe=False)

                url_apple = APPLE_API_ULR + term + APPLE_PARAM
                book = await client.get(url_apple)

                if book.status_code == 200:
                    try:
                        book_result = json.loads(book.text)["results"][0]
                        data = datetime.fromisoformat(book_result["releaseDate"]).strftime(date_format)
                        curr: str = book_result["currency"]
                        price = float(book_result["price"])
                        artist: str = book_result["artistName"]
                        title: str = book_result["trackName"]
                    except KeyError:
                        error_msg = f'Error for row: "{row}" in Apple API.'
                        return JsonResponse(data=error_msg, status=404, safe=False)

                url_nbp = f"{NBP_API_URL}/{curr}/{data}/"
                nbp = await client.get(url_nbp)

                if book.status_code == 200 and nbp.status_code == 200:
                    try:
                        nbp_result: list = json.loads(nbp.text)["rates"][0]
                        rate = float(nbp_result["mid"])
                        no: str = nbp_result["no"]
                    except KeyError:
                        error_msg = f'Error for row: "{row}" in NBP API.'
                        return JsonResponse(data=error_msg, status=404, safe=False)

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
            return JsonResponse(data=search_results, status=200, safe=False)
