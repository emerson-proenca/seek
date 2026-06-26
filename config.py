# config.py

BASE_URL: str = "https://www.subito.it/annunci-italia/vendita/usato/?q="

SEARCH_TERMS: list[str] = [
    "KEH-P7600R",
    "DEQ-9200",
    "DEQ-7600",
    "Pioneer KEH-P8200RDS-W",
    "Pioneer DEQ-9200",
    "Pioneer DEQ-7600",
    "KEH-P8650W",
    "KEH-P8650-W",
    "KEH-P8900R-W",
    "KEH-P8600RW",
    "KEH-P8400R-W",
    "KEH-P8600R-W",
    "KEH-P8200RDS-W",
    "KEH-P7100RDS-W",
    "KEH-P6800R-W",
    "DEQ-44",
    "DEX-P88R",
    "KDS-P505",
    "RD-L110",
    "DEH-P1Y",
    "DEH-P8MP",
    "DEH-P725R-W",
    "725R-W",
    "CDS-P300",
    "Pioneer TS-2150",
    "Pioneer TS-1750",
]

HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.subito.it/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Upgrade-Insecure-Requests": "1",
}
