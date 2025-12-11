"""
NLP 자연어 처리 관련 라우터
"""
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import Response
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import io
import base64

# 공통 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from app.nlp.emma.nlp_service import NLPService
from common.utils import create_response, create_error_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nlp", tags=["nlp"])

# 서비스 인스턴스 생성 (싱글톤 패턴)
_service_instance: Optional[NLPService] = None


def get_service() -> NLPService:
    """NLPService 싱글톤 인스턴스 반환"""
    global _service_instance
    if _service_instance is None:
        _service_instance = NLPService()
    return _service_instance


@router.get("/")
async def nlp_root():
    """NLP 서비스 루트"""
    return create_response(
        data={"service": "mlservice", "module": "nlp", "status": "running"},
        message="NLP Service is running"
    )


# *********
# 말뭉치 관련 엔드포인트
# *********

@router.get("/corpus/fileids")
async def get_corpus_fileids(corpus_name: str = Query(default="gutenberg", description="말뭉치 이름")):
    """말뭉치 파일 ID 목록 반환"""
    try:
        service = get_service()
        fileids = service.get_corpus_fileids(corpus_name)
        return create_response(
            data={"corpus_name": corpus_name, "fileids": fileids},
            message=f"{corpus_name} 말뭉치 파일 목록을 반환했습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"말뭉치 파일 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/corpus/raw")
async def get_corpus_raw(
    corpus_name: str = Query(..., description="말뭉치 이름"),
    fileid: str = Query(..., description="파일 ID"),
    limit: Optional[int] = Query(default=None, description="반환할 문자 수 제한")
):
    """말뭉치 원문 데이터 반환"""
    try:
        service = get_service()
        raw_text = service.get_corpus_raw(corpus_name, fileid)
        
        if limit:
            raw_text = raw_text[:limit]
        
        return create_response(
            data={
                "corpus_name": corpus_name,
                "fileid": fileid,
                "text": raw_text,
                "length": len(raw_text)
            },
            message="말뭉치 원문을 반환했습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"말뭉치 원문 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/corpus/emma")
async def get_emma_raw(
    limit: Optional[int] = Query(default=None, description="반환할 문자 수 제한"),
    generate_wordcloud: bool = Query(default=True, description="워드클라우드 자동 생성 여부")
):
    """제인 오스틴의 엠마 문서 원문 반환 및 워드클라우드 자동 생성"""
    try:
        service = get_service()
        raw_text = service.get_emma_raw()
        
        if limit:
            raw_text = raw_text[:limit]
        
        result_data = {
            "text": raw_text[:1000] if len(raw_text) > 1000 else raw_text,  # 응답 크기 제한
            "length": len(raw_text)
        }
        
        # 워드클라우드 자동 생성
        if generate_wordcloud:
            try:
                # 엠마 문서에서 고유명사(이름) 추출
                stopwords = ["Mr.", "Mrs.", "Miss", "Mr", "Mrs", "Dear"]
                fd_names = service.extract_names_from_corpus("gutenberg", "austen-emma.txt", stopwords)
                
                # 워드클라우드 생성 및 저장
                filepath, wc = service.generate_wordcloud(
                    fd_names,
                    show=False,
                    filename="emma_wordcloud"
                )
                
                result_data["wordcloud"] = {
                    "filepath": filepath,
                    "filename": Path(filepath).name,
                    "most_common": service.get_most_common(fd_names, 10)
                }
            except Exception as wc_error:
                # 워드클라우드 생성 실패해도 텍스트는 반환
                logger.warning(f"워드클라우드 생성 실패: {str(wc_error)}")
                result_data["wordcloud_error"] = str(wc_error)
        
        return create_response(
            data=result_data,
            message="엠마 문서 원문을 반환했습니다" + (" (워드클라우드 생성 완료)" if generate_wordcloud and "wordcloud" in result_data else "")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"엠마 문서 조회 중 오류가 발생했습니다: {str(e)}"
        )


# ************
# 토큰 생성 엔드포인트
# ************

@router.post("/tokenize/sentence")
async def tokenize_sentence(
    request: Dict[str, Any] = Body(..., description="텍스트 데이터")
):
    """문장 단위로 토큰화"""
    try:
        text = request.get("text", "")
        if not text:
            raise ValueError("text 필드가 필요합니다")
        
        service = get_service()
        sentences = service.sentence_tokenize(text)
        
        return create_response(
            data={"sentences": sentences, "count": len(sentences)},
            message="문장 토큰화가 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"문장 토큰화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/tokenize/word")
async def tokenize_word(
    request: Dict[str, Any] = Body(..., description="텍스트 데이터")
):
    """단어 단위로 토큰화"""
    try:
        text = request.get("text", "")
        if not text:
            raise ValueError("text 필드가 필요합니다")
        
        service = get_service()
        tokens = service.word_tokenize(text)
        
        return create_response(
            data={"tokens": tokens, "count": len(tokens)},
            message="단어 토큰화가 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"단어 토큰화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/tokenize/regex")
async def tokenize_regex(
    request: Dict[str, Any] = Body(..., description="텍스트 데이터 및 정규표현식 패턴")
):
    """정규표현식을 사용한 토큰화"""
    try:
        text = request.get("text", "")
        pattern = request.get("pattern", "[\\w]+")
        
        if not text:
            raise ValueError("text 필드가 필요합니다")
        
        service = get_service()
        tokens = service.regex_tokenize(text, pattern)
        
        return create_response(
            data={"tokens": tokens, "count": len(tokens), "pattern": pattern},
            message="정규표현식 토큰화가 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"정규표현식 토큰화 중 오류가 발생했습니다: {str(e)}"
        )


# ***************
# 형태소 분석 엔드포인트
# ***************

@router.post("/stem/porter")
async def porter_stem(
    request: Dict[str, Any] = Body(..., description="단어 또는 단어 리스트")
):
    """Porter Stemmer를 사용한 어간 추출"""
    try:
        words = request.get("words", [])
        if isinstance(words, str):
            words = [words]
        
        if not words:
            raise ValueError("words 필드가 필요합니다")
        
        service = get_service()
        stems = service.porter_stem(words)
        
        return create_response(
            data={"words": words, "stems": stems},
            message="Porter Stemming이 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"어간 추출 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/stem/lancaster")
async def lancaster_stem(
    request: Dict[str, Any] = Body(..., description="단어 또는 단어 리스트")
):
    """Lancaster Stemmer를 사용한 어간 추출"""
    try:
        words = request.get("words", [])
        if isinstance(words, str):
            words = [words]
        
        if not words:
            raise ValueError("words 필드가 필요합니다")
        
        service = get_service()
        stems = service.lancaster_stem(words)
        
        return create_response(
            data={"words": words, "stems": stems},
            message="Lancaster Stemming이 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"어간 추출 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/lemmatize")
async def lemmatize(
    request: Dict[str, Any] = Body(..., description="단어 또는 단어 리스트 및 품사")
):
    """원형 복원 (Lemmatization)"""
    try:
        words = request.get("words", [])
        pos = request.get("pos", None)
        
        if isinstance(words, str):
            words = [words]
        
        if not words:
            raise ValueError("words 필드가 필요합니다")
        
        service = get_service()
        lemmas = service.lemmatize(words, pos)
        
        return create_response(
            data={"words": words, "lemmas": lemmas, "pos": pos},
            message="원형 복원이 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"원형 복원 중 오류가 발생했습니다: {str(e)}"
        )


# **********
# POS 태깅 엔드포인트
# **********

@router.post("/pos/tag")
async def pos_tag(
    request: Dict[str, Any] = Body(..., description="토큰 리스트")
):
    """품사 태깅"""
    try:
        tokens = request.get("tokens", [])
        if isinstance(tokens, str):
            tokens = [tokens]
        
        if not tokens:
            raise ValueError("tokens 필드가 필요합니다")
        
        service = get_service()
        tagged = service.pos_tag(tokens)
        
        return create_response(
            data={"tokens": tokens, "tagged": tagged},
            message="품사 태깅이 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"품사 태깅 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/pos/extract-nouns")
async def extract_nouns(
    request: Dict[str, Any] = Body(..., description="토큰 리스트")
):
    """명사만 추출"""
    try:
        tokens = request.get("tokens", [])
        if isinstance(tokens, str):
            tokens = [tokens]
        
        if not tokens:
            raise ValueError("tokens 필드가 필요합니다")
        
        service = get_service()
        nouns = service.extract_nouns(tokens)
        
        return create_response(
            data={"tokens": tokens, "nouns": nouns, "count": len(nouns)},
            message="명사 추출이 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"명사 추출 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/pos/tokenizer")
async def create_pos_tokenizer(
    request: Dict[str, Any] = Body(..., description="문장")
):
    """품사 정보를 포함한 토크나이저 생성"""
    try:
        sentence = request.get("sentence", "")
        if not sentence:
            raise ValueError("sentence 필드가 필요합니다")
        
        service = get_service()
        pos_tokens = service.create_pos_tokenizer(sentence)
        
        return create_response(
            data={"sentence": sentence, "pos_tokens": pos_tokens},
            message="품사 포함 토크나이저 생성이 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"토크나이저 생성 중 오류가 발생했습니다: {str(e)}"
        )


# ***********
# Text 분석 엔드포인트
# ***********

@router.post("/text/create")
async def create_text_object(
    request: Dict[str, Any] = Body(..., description="토큰 리스트 및 이름")
):
    """NLTK Text 객체 생성"""
    try:
        tokens = request.get("tokens", [])
        name = request.get("name", "Text")
        
        if not tokens:
            raise ValueError("tokens 필드가 필요합니다")
        
        service = get_service()
        text = service.create_text_object(tokens, name)
        
        return create_response(
            data={"name": name, "token_count": len(tokens)},
            message=f"Text 객체 '{name}'가 생성되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Text 객체 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/text/similar")
async def find_similar_words(
    text_name: str = Query(..., description="Text 객체 이름"),
    word: str = Query(..., description="검색할 단어"),
    num: int = Query(default=10, description="반환할 단어 개수")
):
    """유사한 문맥에서 사용된 단어 찾기"""
    try:
        service = get_service()
        similar = service.find_similar_words(text_name, word, num)
        
        return create_response(
            data={"text_name": text_name, "word": word, "similar_words": similar},
            message="유사 단어 검색이 완료되었습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"유사 단어 검색 중 오류가 발생했습니다: {str(e)}"
        )


# ***********
# 빈도 분석 엔드포인트
# ***********

@router.post("/freqdist/create")
async def create_freqdist(
    request: Dict[str, Any] = Body(..., description="토큰 리스트")
):
    """FreqDist 객체 생성"""
    try:
        tokens = request.get("tokens", [])
        if not tokens:
            raise ValueError("tokens 필드가 필요합니다")
        
        service = get_service()
        freqdist = service.create_freqdist(tokens)
        
        # FreqDist를 딕셔너리로 변환
        freq_dict = dict(freqdist)
        
        return create_response(
            data={
                "total_count": freqdist.N(),
                "unique_count": len(freqdist),
                "frequencies": freq_dict
            },
            message="FreqDist 객체가 생성되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"FreqDist 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/freqdist/extract-names")
async def extract_names_from_corpus(
    request: Dict[str, Any] = Body(..., description="말뭉치 정보")
):
    """말뭉치에서 고유명사(이름) 추출"""
    try:
        corpus_name = request.get("corpus_name", "gutenberg")
        fileid = request.get("fileid", "austen-emma.txt")
        stopwords = request.get("stopwords", ["Mr.", "Mrs.", "Miss", "Mr", "Mrs", "Dear"])
        
        service = get_service()
        freqdist = service.extract_names_from_corpus(corpus_name, fileid, stopwords)
        
        # FreqDist를 딕셔너리로 변환
        freq_dict = dict(freqdist)
        
        return create_response(
            data={
                "corpus_name": corpus_name,
                "fileid": fileid,
                "total_count": freqdist.N(),
                "unique_count": len(freqdist),
                "frequencies": freq_dict
            },
            message="고유명사 추출이 완료되었습니다"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"고유명사 추출 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/freqdist/most-common")
async def get_most_common(
    request: Dict[str, Any] = Body(..., description="토큰 리스트 및 개수")
):
    """가장 출현 빈도가 높은 단어 반환"""
    try:
        tokens = request.get("tokens", [])
        num = request.get("num", 10)
        
        if not tokens:
            raise ValueError("tokens 필드가 필요합니다")
        
        service = get_service()
        freqdist = service.create_freqdist(tokens)
        most_common = service.get_most_common(freqdist, num)
        
        return create_response(
            data={
                "most_common": [{"word": word, "count": count} for word, count in most_common],
                "total_count": freqdist.N()
            },
            message="가장 빈번한 단어 조회가 완료되었습니다"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"빈도 분석 중 오류가 발생했습니다: {str(e)}"
        )


# ***********
# 워드클라우드 엔드포인트
# ***********

@router.post("/wordcloud/generate")
async def generate_wordcloud(
    request: Dict[str, Any] = Body(..., description="토큰 리스트 및 워드클라우드 설정")
):
    """워드클라우드 생성 및 이미지 반환"""
    try:
        tokens = request.get("tokens", [])
        width = request.get("width", 1000)
        height = request.get("height", 600)
        background_color = request.get("background_color", "white")
        random_state = request.get("random_state", 0)
        
        if not tokens:
            raise ValueError("tokens 필드가 필요합니다")
        
        service = get_service()
        freqdist = service.create_freqdist(tokens)
        
        # 파일명 생성 (선택적)
        filename = request.get("filename", None)
        
        # 워드클라우드 생성 및 저장
        filepath, wc = service.generate_wordcloud(
            freqdist, 
            width=width, 
            height=height, 
            background_color=background_color,
            random_state=random_state,
            show=False,
            filename=filename
        )
        
        # 이미지를 바이트로 변환
        img_buffer = io.BytesIO()
        wc.to_image().save(img_buffer, format='PNG')
        img_buffer.seek(0)
        img_bytes = img_buffer.getvalue()
        
        # Base64 인코딩
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return create_response(
            data={
                "image_base64": img_base64,
                "filepath": filepath,
                "filename": Path(filepath).name,
                "width": width,
                "height": height,
                "format": "PNG"
            },
            message=f"워드클라우드가 생성되고 저장되었습니다: {filepath}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"워드클라우드 생성 중 오류가 발생했습니다: {str(e)}"
        )

