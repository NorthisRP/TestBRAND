import scrapy
import datetime
import re


class MyuliesSpider(scrapy.Spider):
    name = 'myulies'
    allowed_domains = ['www.wildberries.ru']
    start_url = 'https://www.wildberries.ru'
    pages_count = 9
    cookie_msc = {'__region': '64_75_4_38_30_33_70_1_22_31_66_40_71_69_80_48_68',
                  '__store': '119261_122252_122256_117673_122258_122259_121631_122466_122467_122495_122496_122498_122590_122591_122592_123816_123817_123818_123820_123821_123822_124093_124094_124095_124096_124097_124098_124099_124100_124101_124583_124584_120762_119400_116433_507_3158_120602_6158_117501_121709_2737_117986_1699_1733_686_117413_119070_118106_119781',
                  '__wbl': 'cityId%3D77%26regionId%3D77%26city%3D%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%26phone%3D84957755505%26latitude%3D55%2C7247%26longitude%3D37%2C7882',
                  'ncache': '119261_122252_122256_117673_122258_122259_121631_122466_122467_122495_122496_122498_122590_122591_122592_123816_123817_123818_123820_123821_123822_124093_124094_124095_124096_124097_124098_124099_124100_124101_124583_124584_120762_119400_116433_507_3158_120602_6158_117501_121709_2737_117986_1699_1733_686_117413_119070_118106_119781%3B64_79_4_38_30_33_70_1_22_31_66_40_71_69_80_48_68%3B1.0--%3B12_3_18_15_21%3B0',
                  'route': '37cbd0682b58d8cfb7763ec0d147aa6b90b52d1e'
                  }

    @staticmethod
    def clear_price(string):
        price = string.replace('\xa0', '')
        price = float(re.search(r'\d+', price).group(0))
        return price

    @staticmethod
    def clear_list(some_list):
        new_list = []
        for string in some_list:
            string = string.replace('\n', '').strip()
            new_list.append(string)
        return new_list

    @staticmethod
    def clear_empty_str(some_list):
        new_list = []
        for string in some_list:
            if string:
                new_list.append(string)
        return new_list

    def start_requests(self):
        for page in range(1, 1 + self.pages_count):
            url = f'https://www.wildberries.ru/catalog/obuv/zhenskaya/sabo-i-myuli/myuli?page={page}'
            yield scrapy.Request(url, callback=self.parse_pages, dont_filter=True,
                                 cookies=self.cookie_msc,
                                 meta={'dont_merge_cookies': True})

    def parse_pages(self, response):
        for href in response.xpath("//a[contains(@class, 'ref_goods_n_p')]/@href").extract():
            url = self.start_url + href
            yield scrapy.Request(url, callback=self.parse, dont_filter=True,
                                 cookies=self.cookie_msc,
                                 meta={'dont_merge_cookies': True})

    def parse(self, response, **kwargs):
        RPC = response.xpath("//div[@class='article']/span/text()").extract_first()
        color = response.xpath("//span[@class='color']/text()").extract_first()
        title = " / ".join(response.xpath("//div[@class='brand-and-name j-product-title']/span/text()").extract())
        if color:
            title += ", " + color
        marketing_tags = MyuliesSpider.clear_empty_str(MyuliesSpider.clear_list(
            response.xpath("//li[contains(@class, 'about-advantages-item')]/text()").extract()))
        brand = response.xpath("//span[@class='brand']/text()").extract_first()
        section = response.xpath("//ul[@class='tags-group-list j-tags-list']/li/a/text()").extract()

        # сформируем данные о ценах
        current_price = MyuliesSpider.clear_price(
            response.xpath("//span[@class='final-cost']/text()").extract_first())
        old_price = response.xpath(
            "//span[contains(@class, 'old-price')]/del/text()").extract_first()  # .replace('\xa0', '')
        sale = 0
        if old_price:
            old_price = MyuliesSpider.clear_price(old_price)
            sale = round(current_price / old_price * 100)
        else:
            old_price = current_price
        price_data = {"current": current_price, "original": old_price, "sale_tag": f'Скидка {sale}%'}

        # сформируем данные о стоке
        in_stock = bool(response.xpath(
            "//button[contains(text(), 'Добавить в корзину') and not(contains(@class, 'hide'))]").extract())

        # сформируем данные о картинках
        main_image = response.xpath("//img[contains(@class, 'preview-photo')]/@src").extract_first()
        set_images = response.xpath("//span[contains(@class, 'slider-content')]/img/@src").extract()

        # сформируем метаданные
        key_data = response.xpath("//div[contains(@class, 'pp')]/span/b/text()").extract()
        value_data = MyuliesSpider.clear_list(response.xpath("//div[contains(@class, 'pp')]/span/text()").extract())
        metadata = {"АРТИКУЛ": RPC, "Цвет": color}
        metadata.update({key_data[i]: value_data[i] for i in range(len(key_data))})

        variants = len(response.xpath("//li[contains(@class, 'swiper-slide')]/a").extract())

        item = {
            "timestamp": datetime.datetime.now().timestamp(),
            "RPC": RPC,
            "url": response.url,
            "title": title,
            "marketing_tags": marketing_tags,
            "brand": brand,
            "section": section,
            "price_data": price_data,
            "stock": {
                "in_stock": in_stock,
                "count": 0
            },
            "assets": {
                "main_image": main_image,
                "set_images": set_images,
                "view360": [],
                "video": []
            },
            "metadata": metadata,
            "variants": variants
        }
        yield item
