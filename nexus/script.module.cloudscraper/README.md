# script.module.cloudscraper

Venomous cloudscraper repacked for Kodi 18+.

Basic usage: 
```
from cloudscraper2 import CloudScraper
scraper = CloudScraper()
```

or

```
import cloudscraper2
scraper = cloudscraper2.create_scraper()
```


To retrieve and use CF cookies in requests:
```
from cloudscraper2 import CloudScraper
scraper = CloudScraper.create_scraper()
ua = 'My_user_agent'
scraper.headers.update({'User-Agent': ua})
cookies = scraper.get('My_url').cookies.get_dict()
headers = {'User-Agent': ua}
req = requests.get('My_new_url', cookies=cookies, headers=headers)
```



For more info see here: https://github.com/VeNoMouS/cloudscraper
