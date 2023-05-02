import requests
from bs4 import BeautifulSoup
import pandas as pd


class Tabelog:
    def __init__(self, base_url):

        # 変数宣言
        self.store_id_num = 0
        self.store_name = ""
        self.station = ""
        self.address = ""
        self.latitude = 0
        self.longitude = 0
        self.review_cnt = 0
        self.review_list = list(range(10))
        self.columns = ["store_id", "store_name", "station", "address", "review_cnt", "latitude", "longtitude",
                        "review_1", "review_2", "review_3", "review_4", "review_5",
                        "review_6", "review_7", "review_8", "review_9", "review_10"] # 店名、最寄駅、住所、レビュー件数(最大10件)、レビュー内容

        self.df = pd.DataFrame(columns=self.columns)

        self.scrape_list(base_url)


    def scrape_list(self, list_url):
        ### 引数で渡したURLへ遷移 ###
        r = requests.get(list_url) # データ取得
        if r.status_code != requests.codes.ok:
            return False

        soup = BeautifulSoup(r.content, 'html.parser') # データ抽出,子要素の取得
        soup_a_list = soup.find_all('a', class_='list-rst__rst-name-target', limit=10) # 店名一覧

        if len(soup_a_list) == 0:
            return False

        for soup_a in soup_a_list:
            item_url = soup_a.get('href') # 店の個別ページURLを取得
            self.store_id_num += 1

            self.store_name = soup_a.contents[0] # 店名を抽出

            self.scrape_item(item_url)

        return True


    def scrape_item(self, item_url):
        ### 各店のページへ遷移 ###
        pick_r = requests.get(item_url) # データ取得
        if pick_r.status_code != requests.codes.ok: #もし存在しないリンクを踏んだらエラーを返す
            return False

        pick_soup = BeautifulSoup(pick_r.content, 'html.parser', from_encoding='utf-8') # データ抽出,子要素の取得

        ll= pick_soup.find("script",{"type" : "application/ld+json"}).string
        lat_st = ll.find("latitude")+10
        lat_ed = ll.find(",",lat_st)
        self.latitude = ll[lat_st:lat_ed] # 店舗緯度取得
        lon_st = ll.find("longitude")+11
        lon_ed = ll.find("}",lon_st)
        self.longitude = ll[lon_st:lon_ed] # 店舗経度取得

        self.station = pick_soup.find('span', class_="linktree__parent-target-text").contents[0] # 最寄駅を抽出

        pick_address = pick_soup.find('p', class_="rstinfo-table__address").contents  # 店の住所を抽出
        _address = ""
        for address in pick_address:
            _address += address.getText()
        self.address = _address.replace(" ", "")

        ### 口コミページへ遷移 ###
        pick_url = pick_soup.select("#review")[0].get("href") # 口コミへ飛ぶURL
        pick_comment = requests.get(pick_url) # 口コミページのデータ取得
        if pick_comment.status_code != requests.codes.ok:
            return False

        pick_comment_soup = BeautifulSoup(pick_comment.content, 'html.parser') # データ抽出,子要素の取得

        ### 題名と全文を拾う ###

        pick_link_list = pick_comment_soup.find_all('a', class_="rvw-item__title-target", limit=10) # 口コミの詳細に飛ぶリンク、ここでは最大10
        self.review_cnt = len(pick_link_list) # 抽出したレビューの件数
        for i in range(len(pick_link_list)):
            link = "https://tabelog.com" + pick_link_list[i].get('href') # リンクを組む
            full_comment = requests.get(link) # 個々人の口コミのデータ取得
            if full_comment.status_code != requests.codes.ok:
                return False

            full_comment_soup = BeautifulSoup(full_comment.content, 'html.parser') # データ抽出,子要素の取得
            full_comment_title = full_comment_soup.find_all('p', class_="rvw-item__title", limit=1) #　何回通っていても拾う題名は1つのみ
            full_comment_title = full_comment_title[0].getText()
            full_comment_text = full_comment_soup.find_all('div', class_="rvw-item__rvw-comment rvw-item__rvw-comment--custom", limit=1) #　同じく拾うコメントは1つのみ
            full_comment_text = full_comment_text[0].getText()
            self.review_list[i] = full_comment_title + full_comment_text

        self.make_df()

        return


    def make_df(self):
        self.store_id = str(self.store_id_num).zfill(8) #0パディング
        se = pd.Series([self.store_id, self.store_name, self.station, self.address, self.review_cnt, self.latitude, self.longitude,
                        self.review_list[0], self.review_list[1], self.review_list[2],self.review_list[3], self.review_list[4],
                        self.review_list[5],self.review_list[6], self.review_list[7], self.review_list[8], self.review_list[9]],
                        self.columns) # 行を作成
        self.df = pd.concat([self.df, pd.DataFrame(se).T])
        # self.df = self.df.append(se, self.columns) # 最新のpandasでなければappendも使える (はず)

        return


def main():
    tokyo_ramen_review = Tabelog(base_url="https://tabelog.com/tokyo/R9/rstLst/ramen/1/?SrtT=rt")
    # A1301 ~ A1331 が　東京の地域別
    # C13101 ~ C13123 が　東京の23区
    # Rから始まる路線別もあるがコードが並んでいない e.g. 山手線=R9、日比谷線=R1096)
    # ramenの後の数字がページ番号 (最大でも60pしか表示されないらしい)
    # SrtTの引数でソートしている、rtはランキングでrvcnが口コミ人数

    tokyo_ramen_review.df.to_csv("output/tokyo_ramen_review_A1301_1.csv",  index=False, encoding="utf_8_sig") # CSV保存

main()
