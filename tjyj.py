from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, NoSuchFrameException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from itertools import product
import pandas as pd
# from time import sleep
# from random import uniform


def get_articles(start_date, end_date, largest_index=30):
    start_year, start_month = start_date.split('-')
    end_year, end_month = end_date.split('-')

    start_year = int(start_year)
    start_month = int(start_month)
    end_year = int(end_year)
    end_month = int(end_month)

    articles_ = []
    n_years = end_year - start_year + 1
    indexes = [str(index).zfill(3) for index in range(largest_index + 1)]
    if n_years == 1:
        months = [str(month).zfill(2) for month in range(start_month, end_month + 1)]
        for month, index in product(months, indexes):
            articles_.append(str(start_year) + month + index)
    elif n_years == 2:
        months_1 = [str(month).zfill(2) for month in range(start_month, 13)]
        months_2 = [str(month).zfill(2) for month in range(1, end_month + 1)]
        for month, index in product(months_1, indexes):
            articles_.append(str(start_year) + month + index)
        for month, index in product(months_2, indexes):
            articles_.append(str(end_year) + month + index)
    else:
        years = [str(year) for year in range(start_year + 1, end_year)]
        months_1 = [str(month).zfill(2) for month in range(start_month, 13)]
        months_2 = [str(month).zfill(2) for month in range(1, 13)]
        months_3 = [str(month).zfill(2) for month in range(1, end_month + 1)]
        for month, index in product(months_1, indexes):
            articles_.append(str(start_year) + month + index)
        for year, month, index in product(years, months_2, indexes):
            articles_.append(year + month + index)
        for month, index in product(months_3, indexes):
            articles_.append(str(end_year) + month + index)

    return articles_


def get_next_article_index(article_index_, articles_, state, patience=2):
    if state == 'success':
        next_index = article_index_ + 1
        if next_index < len(articles_):
            return next_index
        else:
            return None
    elif state == 'fail':
        article_ = articles_[article_index_]

        year = int(article_[:4])
        month = int(article_[4:6])
        index = int(article_[6:])

        if int(index) < patience:
            next_article = str(year) + str(month).zfill(2) + str(index + 1).zfill(3)
        elif int(index) == patience or month == 12:
            next_article = str(year + 1) + '01000'
        else:
            next_article = str(year) + str(month + 1).zfill(2) + '000'

        try:
            return articles_.index(next_article)
        except ValueError:
            return None
    else:
        raise ValueError


def get_article_info(article_):
    global driver, wait  # ???driver?????????????????????????????????????????????????????????????????????

    year = int(article_[:4])
    if 1994 <= year <= 1999:
        article_ = str(year - 1990) + article_[4:6] + '.' + article_[6:]

    url = 'https://kns8.cnki.net/KCMS/detail/detail.aspx?dbcode=CJFD&filename=TJYJ' + article_
    driver.get(url)

    # ??????????????????????????????????????????????????????
    try:
        title = driver.find_element_by_css_selector('h1').text
    except NoSuchElementException:
        return None

    # ??????????????????????????????
    authors = driver.find_elements_by_css_selector('#authorpart a')
    if not authors:
        authors = driver.find_elements_by_css_selector('#authorpart span')
    if not authors:
        return pd.DataFrame()

    # ???????????????????????????????????????
    try:
        authors = [author.text[:-len(author.find_element_by_css_selector('sup').text)] for author in authors]
    except NoSuchElementException:
        authors = [author.text for author in authors]
    authors = '; '.join(authors)

    # ????????????
    departments = driver.find_elements_by_css_selector('a.author')
    if not departments:
        departments = driver.find_elements_by_css_selector('#authorpart+ h3 span')
    departments = [department.text for department in departments]
    if departments and departments[0][1] == '.':
        departments = [department[3:] for department in departments]
    departments = '; '.join(departments)

    # ???????????????
    try:
        journal_name = driver.find_element_by_css_selector('.top-tip a:nth-child(1)').text
    except NoSuchElementException:
        journal_name = None

    # ??????????????????
    try:
        publish_time = driver.find_element_by_css_selector('.top-tip a+ a').text
    except NoSuchElementException:
        publish_time = None

    # ????????????
    try:
        n_page = driver.find_element_by_css_selector('.total-inform span:nth-child(3)').text
        if '?????????' in n_page:
            n_page = int(n_page.replace('?????????', ''))
        else:
            n_page = None
    except NoSuchElementException:
        n_page = None

    # ????????????
    try:
        pages = driver.find_element_by_css_selector('.total-inform span:nth-child(2)').text
        if '?????????' in pages:
            pages = pages.replace('?????????', '')
        else:
            if '?????????' in pages:
                n_page = int(pages.replace('?????????', ''))
            pages = None
    except NoSuchElementException:
        pages = None

    # ????????????
    try:
        abstract = driver.find_element_by_css_selector('#ChDivSummary').text
    except NoSuchElementException:
        abstract = None

    # ???????????????
    keywords = driver.find_elements_by_css_selector('.keywords a')
    keywords = '; '.join([keyword.text.replace(';', '') for keyword in keywords])

    # ??????????????????
    funds = driver.find_elements_by_css_selector('.funds a')
    funds = '; '.join([fund.text.replace('???', '') for fund in funds])

    # ??????DOI
    try:
        DOI = driver.find_element_by_css_selector('.top-space:nth-child(1) p').text
    except NoSuchElementException:
        DOI = None

    # ????????????
    try:
        album = driver.find_element_by_css_selector('.top-space:nth-child(2) p').text
    except NoSuchElementException:
        album = None

    # ????????????
    try:
        theme = driver.find_element_by_css_selector('.top-space:nth-child(3) p').text
    except NoSuchElementException:
        theme = None

    # ???????????????
    try:
        category = driver.find_element_by_css_selector('.top-space:nth-child(4) p').text
    except NoSuchElementException:
        category = None

    # ???????????????
    try:
        n_download = driver.find_element_by_css_selector('#DownLoadParts span:nth-child(1)').text
        n_download = int(n_download.replace('?????????', ''))
    except NoSuchElementException:
        n_download = None

    # ???????????????
    while True:
        try:
            n_cited = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#rc3'))).text
            n_cited = int(n_cited[1:-1])
            break
        except TimeoutException:
            driver.refresh()
        except (NoSuchElementException, ValueError):
            n_cited = None
            break

    # ???????????????
    while True:
        try:
            n_cite = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#rc1'))).text
            n_cite = int(n_cite[1:-1])
            break
        except TimeoutException:
            driver.refresh()
        except (NoSuchElementException, ValueError):
            n_cite = None
            break

    # ??????????????????
    references = []
    if n_cite and n_cite > 0:
        while True:
            try:
                driver.switch_to.frame('frame1')
                essay_boxes = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'essayBox')))
                for i in range(len(essay_boxes)):
                    while True:
                        additional_references = essay_boxes[i].find_elements_by_css_selector('li')
                        additional_references = [
                            additional_reference.text[4:] for additional_reference in additional_references
                        ]
                        references.extend(additional_references)

                        try:
                            next_page = essay_boxes[i].find_element_by_link_text('?????????')
                            driver.execute_script("arguments[0].click();", next_page)
                            essay_boxes = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'essayBox')))
                        except NoSuchElementException:
                            break
                break
            except TimeoutException:
                driver.refresh()
            except NoSuchFrameException:
                break
    references = ';; '.join(references)

    # ????????????
    article_info_ = {
        '??????': title,
        '??????': authors,
        '??????': departments,
        '?????????': journal_name,
        '????????????': publish_time,
        '??????': pages,
        '??????': n_page,
        '??????': abstract,
        '?????????': keywords,
        '????????????': funds,
        'DOI': DOI,
        '??????': album,
        '??????': theme,
        '?????????': category,
        '?????????': n_download,
        '?????????': n_cited,
        '?????????': n_cite,
        '????????????': references,
        '??????': url
    }

    # ????????????????????????
    article_info_ = pd.DataFrame(article_info_, index=[article_])

    # ??????????????????????????????
    # sleep(uniform(3, 5))

    return article_info_


if __name__ == '__main__':
    articles = get_articles(start_date='1984-01', end_date='1999-12')

    article_infos = pd.DataFrame()
    driver = webdriver.Chrome(ChromeDriverManager().install())
    wait = WebDriverWait(driver, 20)

    article_index = 0
    while True:
        article = articles[article_index]
        article_info = get_article_info(article)
        if article_info is not None:
            article_infos = article_infos.append(article_info)
            article_infos.to_csv('????????????_??????.csv', index=False, encoding='utf_8_sig')  # ??????????????????????????????????????????????????????????????????????????????
            article_index = get_next_article_index(article_index, articles, 'success')
        else:
            article_index = get_next_article_index(article_index, articles, 'fail')
        if not article_index:
            break

    driver.quit()

    # article_infos.to_csv('????????????_??????.csv', index=False, encoding='utf_8_sig')
