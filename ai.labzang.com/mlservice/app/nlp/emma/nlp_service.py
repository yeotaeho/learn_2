# ************
# NLTK 자연어 처리 패키지
# ************
"""
https://datascienceschool.net/view-notebook/118731eec74b4ad3bdd2f89bab077e1b/
NLTK(Natural Language Toolkit) 패키지는 
교육용으로 개발된 자연어 처리 및 문서 분석용 파이썬 패키지다. 
다양한 기능 및 예제를 가지고 있으며 실무 및 연구에서도 많이 사용된다.
NLTK 패키지가 제공하는 주요 기능은 다음과 같다.
말뭉치
토큰 생성
형태소 분석
품사 태깅
"""

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize, RegexpTokenizer
from nltk.stem import PorterStemmer, LancasterStemmer, WordNetLemmatizer
from nltk.tag import pos_tag, untag
from nltk import Text, FreqDist
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
from pathlib import Path
from datetime import datetime


class NLPService:
    """
    NLTK를 활용한 자연어 처리 서비스 클래스
    
    말뭉치, 토큰 생성, 형태소 분석, 품사 태깅 등의 기능을 제공합니다.
    """
    
    def __init__(self, download_book: bool = True):
        """
        NLPService 초기화
        
        Args:
            download_book: NLTK book 데이터 다운로드 여부 (기본값: True)
        """
        # 필요한 NLTK 데이터 다운로드
        try:
            nltk.download('averaged_perceptron_tagger_eng', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('wordnet', quiet=True)
        except:
            pass
        
        if download_book:
            nltk.download('book', quiet=True)
        
        # 토크나이저 초기화
        self.regex_tokenizer = RegexpTokenizer(r"[\w]+")
        
        # 형태소 분석기 초기화
        self.porter_stemmer = PorterStemmer()
        self.lancaster_stemmer = LancasterStemmer()
        self.lemmatizer = WordNetLemmatizer()
        
        # Text 객체 저장용
        self.text_objects = {}
    
    # *********
    # 말뭉치 관련 메서드
    # *********
    
    def get_corpus_fileids(self, corpus_name: str = "gutenberg"):
        """
        말뭉치 파일 ID 목록 반환
        
        Args:
            corpus_name: 말뭉치 이름 (기본값: "gutenberg")
            
        Returns:
            말뭉치 파일 ID 리스트
        """
        corpus = getattr(nltk.corpus, corpus_name, None)
        if corpus:
            return corpus.fileids()
        return []
    
    def get_corpus_raw(self, corpus_name: str, fileid: str):
        """
        말뭉치 원문 데이터 반환
        
        Args:
            corpus_name: 말뭉치 이름
            fileid: 파일 ID
            
        Returns:
            원문 문자열
        """
        corpus = getattr(nltk.corpus, corpus_name, None)
        if corpus:
            return corpus.raw(fileid)
        return ""
    
    def get_emma_raw(self):
        """
        제인 오스틴의 엠마 문서 원문 반환
        
        Returns:
            엠마 문서 원문 문자열
        """
        return self.get_corpus_raw("gutenberg", "austen-emma.txt")
    
    # ************
    # 토큰 생성 메서드
    # ************
    
    def sentence_tokenize(self, text: str):
        """
        문장 단위로 토큰화
        
        Args:
            text: 입력 텍스트
            
        Returns:
            문장 리스트
        """
        return sent_tokenize(text)
    
    def word_tokenize(self, text: str):
        """
        단어 단위로 토큰화
        
        Args:
            text: 입력 텍스트
            
        Returns:
            단어 토큰 리스트
        """
        return word_tokenize(text)
    
    def regex_tokenize(self, text: str, pattern: str = r"[\w]+"):
        """
        정규표현식을 사용한 토큰화
        
        Args:
            text: 입력 텍스트
            pattern: 정규표현식 패턴 (기본값: "[\w]+")
            
        Returns:
            토큰 리스트
        """
        tokenizer = RegexpTokenizer(pattern)
        return tokenizer.tokenize(text)
    
    # ***************
    # 형태소 분석 메서드
    # ***************
    
    def porter_stem(self, words):
        """
        Porter Stemmer를 사용한 어간 추출
        
        Args:
            words: 단어 또는 단어 리스트
            
        Returns:
            어간 추출 결과 리스트
        """
        if isinstance(words, str):
            words = [words]
        return [self.porter_stemmer.stem(w) for w in words]
    
    def lancaster_stem(self, words):
        """
        Lancaster Stemmer를 사용한 어간 추출
        
        Args:
            words: 단어 또는 단어 리스트
            
        Returns:
            어간 추출 결과 리스트
        """
        if isinstance(words, str):
            words = [words]
        return [self.lancaster_stemmer.stem(w) for w in words]
    
    def lemmatize(self, words, pos: str = None):
        """
        원형 복원 (Lemmatization)
        
        Args:
            words: 단어 또는 단어 리스트
            pos: 품사 태그 (기본값: None)
            
        Returns:
            원형 복원 결과 리스트
        """
        if isinstance(words, str):
            words = [words]
        
        if pos:
            return [self.lemmatizer.lemmatize(w, pos=pos) for w in words]
        return [self.lemmatizer.lemmatize(w) for w in words]
    
    # **********
    # POS tagging 메서드
    # **********
    
    def get_pos_tag_help(self, tag: str):
        """
        품사 태그 설명 보기
        
        Args:
            tag: 품사 태그 (예: 'VB', 'NN')
        """
        nltk.help.upenn_tagset(tag)
    
    def pos_tag(self, tokens):
        """
        품사 태깅
        
        Args:
            tokens: 토큰 리스트
            
        Returns:
            (토큰, 품사) 튜플 리스트
        """
        return pos_tag(tokens)
    
    def extract_nouns(self, tokens):
        """
        명사만 추출
        
        Args:
            tokens: 토큰 리스트
            
        Returns:
            명사 토큰 리스트
        """
        tagged_list = self.pos_tag(tokens)
        return [t[0] for t in tagged_list if t[1] == "NN"]
    
    def remove_tags(self, tagged_list):
        """
        품사 태그 제거
        
        Args:
            tagged_list: (토큰, 품사) 튜플 리스트
            
        Returns:
            토큰 리스트
        """
        return untag(tagged_list)
    
    def create_pos_tokenizer(self, sentence: str):
        """
        품사 정보를 포함한 토크나이저 생성
        
        Args:
            sentence: 입력 문장
            
        Returns:
            품사가 포함된 토큰 리스트 (형식: "토큰/품사")
        """
        tokens = self.word_tokenize(sentence)
        tagged_list = self.pos_tag(tokens)
        return ["/".join(p) for p in tagged_list]
    
    # ***********
    # Text 클래스 관련 메서드
    # ***********
    
    def create_text_object(self, tokens, name: str = "Text"):
        """
        NLTK Text 객체 생성
        
        Args:
            tokens: 토큰 리스트
            name: Text 객체 이름
            
        Returns:
            Text 객체
        """
        text = Text(tokens, name=name)
        self.text_objects[name] = text
        return text
    
    def plot_word_frequency(self, text_name: str, num_words: int = 20):
        """
        단어 사용 빈도 그래프 그리기
        
        Args:
            text_name: Text 객체 이름
            num_words: 표시할 단어 개수
        """
        if text_name in self.text_objects:
            self.text_objects[text_name].plot(num_words)
            plt.show()
    
    def dispersion_plot(self, text_name: str, words: list):
        """
        단어 사용 위치 시각화
        
        Args:
            text_name: Text 객체 이름
            words: 시각화할 단어 리스트
        """
        if text_name in self.text_objects:
            self.text_objects[text_name].dispersion_plot(words)
    
    def concordance(self, text_name: str, word: str, lines: int = 5):
        """
        단어 사용 위치 표시
        
        Args:
            text_name: Text 객체 이름
            word: 검색할 단어
            lines: 표시할 줄 수
        """
        if text_name in self.text_objects:
            self.text_objects[text_name].concordance(word, lines=lines)
    
    def find_similar_words(self, text_name: str, word: str, num: int = 10):
        """
        유사한 문맥에서 사용된 단어 찾기
        
        Args:
            text_name: Text 객체 이름
            word: 검색할 단어
            num: 반환할 단어 개수
            
        Returns:
            유사 단어 리스트
        """
        if text_name in self.text_objects:
            return self.text_objects[text_name].similar(word, num)
        return []
    
    def find_collocations(self, text_name: str, num: int = 10):
        """
        연어(collocation) 찾기
        
        Args:
            text_name: Text 객체 이름
            num: 반환할 연어 개수
        """
        if text_name in self.text_objects:
            self.text_objects[text_name].collocations(num)
    
    # ***********
    # FreqDist 관련 메서드
    # ***********
    
    def get_vocab(self, text_name: str):
        """
        Text 객체의 어휘 빈도 분포 반환
        
        Args:
            text_name: Text 객체 이름
            
        Returns:
            FreqDist 객체
        """
        if text_name in self.text_objects:
            return self.text_objects[text_name].vocab()
        return None
    
    def create_freqdist(self, tokens):
        """
        FreqDist 객체 생성
        
        Args:
            tokens: 토큰 리스트
            
        Returns:
            FreqDist 객체
        """
        return FreqDist(tokens)
    
    def extract_names_from_corpus(self, corpus_name: str, fileid: str, 
                                   stopwords: list = None):
        """
        말뭉치에서 고유명사(이름) 추출
        
        Args:
            corpus_name: 말뭉치 이름
            fileid: 파일 ID
            stopwords: 제외할 단어 리스트
            
        Returns:
            FreqDist 객체
        """
        if stopwords is None:
            stopwords = ["Mr.", "Mrs.", "Miss", "Mr", "Mrs", "Dear"]
        
        raw_text = self.get_corpus_raw(corpus_name, fileid)
        tokens = self.regex_tokenize(raw_text)
        tagged_tokens = self.pos_tag(tokens)
        
        names_list = [
            t[0] for t in tagged_tokens 
            if t[1] == "NNP" and t[0] not in stopwords
        ]
        
        return self.create_freqdist(names_list)
    
    def get_word_stats(self, freqdist, word: str):
        """
        단어 통계 정보 반환
        
        Args:
            freqdist: FreqDist 객체
            word: 단어
            
        Returns:
            (전체 단어 수, 단어 출현 횟수, 단어 출현 확률) 튜플
        """
        return freqdist.N(), freqdist[word], freqdist.freq(word)
    
    def get_most_common(self, freqdist, num: int = 10):
        """
        가장 출현 빈도가 높은 단어 반환
        
        Args:
            freqdist: FreqDist 객체
            num: 반환할 단어 개수
            
        Returns:
            (단어, 빈도) 튜플 리스트
        """
        return freqdist.most_common(num)
    
    # ***********
    # 워드클라우드 메서드
    # ***********
    
    def generate_wordcloud(self, freqdist, width: int = 1000, 
                          height: int = 600, background_color: str = "white",
                          random_state: int = 0, show: bool = True,
                          filename: str = None, save_path: str = None):
        """
        워드클라우드 생성 및 표시
        
        Args:
            freqdist: FreqDist 객체
            width: 이미지 너비
            height: 이미지 높이
            background_color: 배경색
            random_state: 랜덤 시드
            show: 그래프 표시 여부
            filename: 저장할 파일명 (기본값: None, 자동 생성)
            save_path: 저장할 폴더 경로 (기본값: None, app/nlp/save 사용)
            
        Returns:
            WordCloud 객체와 저장된 파일 경로 튜플 (filepath, WordCloud)
        """
        wc = WordCloud(
            width=width, 
            height=height, 
            background_color=background_color, 
            random_state=random_state
        )
        wc.generate_from_frequencies(freqdist)
        
        # 저장 경로 설정
        if save_path is None:
            # 현재 파일의 위치를 기준으로 save 폴더 찾기
            current_file = Path(__file__).resolve()
            save_dir = current_file.parent.parent / "save"
        else:
            save_dir = Path(save_path)
        
        # save 폴더가 없으면 생성
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일명 생성
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"wordcloud_{timestamp}.png"
        elif not filename.endswith('.png'):
            filename = f"{filename}.png"
        
        # 전체 파일 경로
        filepath = save_dir / filename
        
        # 이미지 저장
        wc.to_file(str(filepath))
        
        if show:
            plt.imshow(wc)
            plt.axis("off")
            plt.show()
        
        return str(filepath), wc


# 사용 예제
if __name__ == "__main__":
    # 서비스 인스턴스 생성
    nlp_service = NLPService()
    
    # 엠마 문서 가져오기
    emma_raw = nlp_service.get_emma_raw()
    print(emma_raw[:1302])
    
    # 문장 토큰화 예제
    sentences = nlp_service.sentence_tokenize(emma_raw[:1000])
    print(sentences[3])
    
    # 단어 토큰화 예제
    words = nlp_service.word_tokenize(emma_raw[50:100])
    print(words)
    
    # 정규표현식 토큰화 예제
    regex_tokens = nlp_service.regex_tokenize(emma_raw[50:100])
    print(regex_tokens)
    
    # 형태소 분석 예제
    test_words = ['lives', 'crying', 'flies', 'dying']
    print("Porter Stemming:", nlp_service.porter_stem(test_words))
    print("Lancaster Stemming:", nlp_service.lancaster_stem(test_words))
    print("Lemmatization:", nlp_service.lemmatize(test_words))
    print("Lemmatization (verb):", nlp_service.lemmatize("dying", pos="v"))
    
    # POS 태깅 예제
    sentence = "Emma refused to permit us to obtain the refuse permit"
    tokens = nlp_service.word_tokenize(sentence)
    tagged = nlp_service.pos_tag(tokens)
    print("POS Tagged:", tagged)
    
    # 명사 추출
    nouns = nlp_service.extract_nouns(tokens)
    print("Nouns:", nouns)
    
    # 품사 포함 토크나이저
    pos_tokens = nlp_service.create_pos_tokenizer(sentence)
    print("POS Tokenizer:", pos_tokens)
    
    # Text 객체 생성 및 분석
    emma_tokens = nlp_service.regex_tokenize(emma_raw)
    text = nlp_service.create_text_object(emma_tokens, name="Emma")
    
    # 단어 빈도 그래프
    # nlp_service.plot_word_frequency("Emma", 20)
    
    # 분산 플롯
    # nlp_service.dispersion_plot("Emma", ["Emma", "Knightley", "Frank", "Jane", "Harriet", "Robert"])
    
    # 유사 단어 찾기
    similar = nlp_service.find_similar_words("Emma", "Emma", 10)
    print("Similar words:", similar)
    
    # 연어 찾기
    # nlp_service.find_collocations("Emma", 10)
    
    # FreqDist 예제
    stopwords = ["Mr.", "Mrs.", "Miss", "Mr", "Mrs", "Dear"]
    fd_names = nlp_service.extract_names_from_corpus("gutenberg", "austen-emma.txt", stopwords)
    
    # 통계 정보
    stats = nlp_service.get_word_stats(fd_names, "Emma")
    print(f"Total words: {stats[0]}, Emma count: {stats[1]}, Emma freq: {stats[2]}")
    
    # 가장 빈번한 단어
    most_common = nlp_service.get_most_common(fd_names, 5)
    print("Most common:", most_common)
    
    # 워드클라우드 생성 및 저장
    filepath, wc = nlp_service.generate_wordcloud(fd_names, show=False)
    print(f"워드클라우드가 저장되었습니다: {filepath}")
