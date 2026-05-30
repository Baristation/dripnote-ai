from langchain_core.tools import tool


@tool
def search_website_docs(query: str) -> str:
    """
    Baristation 웹사이트 이용 방법, 주문, 배송, 회원, 결제 관련 문서를 검색한다.
    사이트 사용법·서비스 정책 질문 시 사용한다.
    """
    # TODO: 웹사이트 메뉴얼 Qdrant 컬렉션 구축 후 실제 검색 구현
    return "현재 사이트 이용 안내 검색 기능을 준비 중입니다. 자세한 사항은 고객센터에 문의해 주세요."
