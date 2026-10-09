# policy-research-kit 소개영상

연구자·실무자를 위한 30초 한국어 모션그래픽입니다. 무음으로 제작했으며, 핵심 내용을 화면에 표시합니다.
정책한걸음 최종 로고에서 추출한 파랑·남색·회색, 연결 곡선과 굵은 제목을 적용했습니다.
[디자인 기준](../../DESIGN.md) · [브랜드 보드](brand-board.png) · [색상 토큰](brand-tokens.json)

공개 문서·코드의 사용 흐름을 도식화했습니다. 실제 UI나 AI 실행 화면을 녹화한 영상은 아닙니다.

- [MP4 영상](intro.mp4): 1920×1080, 30fps, H.264, 30초
- [README 미리보기 GIF](intro-preview.gif): 처리·결과 장면 9초, 960×540, 10fps
- [정지 포스터](intro-poster.png) · [5개 장면 전체](intro-storyboard.png)
- [내용 데이터](intro.json) · [렌더 스크립트](render_intro.py)

## 영상 대본

| 시간 | 전달할 내용 |
|---|---|
| 0–4초 | 보고서의 근거를, 다시 찾을 수 있도록. — 설계·조사·집필·검수를 연결하는 연구 흐름 |
| 4–11초 | 입력: 연구 주제·요청사항 + 메모·통계·참고자료. 정책연구 주제와 참고자료를 보고서 초안 및 검수 기록으로 발전시킬 때 |
| 11–20초 | 설계·점검 → 목차 확인 → 조사·집필 → 별도 검수. 결과: 보고서 초안 + 근거 목록 + 검수 기록 |
| 20–26초 | 집필과 검수의 역할을 나눕니다 |
| 26–30초 | 주제와 보유 자료에서 시작하세요 |

요청·사용 예시:

```text
지역 인력정책 보고서를 준비해줘.
첨부한 메모와 통계를 바탕으로
목차와 조사계획부터 보여줘.
```

강점 장면의 자막:

- **설계 때 한 번**: 목차·연구 질문·분석틀 점검
- **초안 뒤 한 번**: 읽기 전용 검토 역할로 교차 확인
- **근거를 파일로**: 조사·수정 기록을 남겨 역추적

사용 범위: AI 검수가 정확성을 보증하지는 않습니다. HWPX 출력에는 별도 도구가 필요합니다.

## 설명의 근거와 확인 범위

기준 소스 커밋: `b884ec87c73128cfec5a9c1f0b06ced8998ccae1`. 영상 길이는 작업 소요시간이나 성능 수치를 뜻하지 않습니다.

- [agents/policy-report-reviewer.md](../../agents/policy-report-reviewer.md)
- [agents/policy-research-investigator.md](../../agents/policy-research-investigator.md)
- [docs/vanilla-vs-kit.md](../../docs/vanilla-vs-kit.md)

검토 역할 정의의 읽기 전용 도구 제한, 설계·초안의 두 점검 단계와 근거 목록 출력을 확인했습니다. 새 보고서 전체를 생성하는 성능 실험은 수행하지 않았습니다.

## 다시 만들기

Python 3.9 이상, Pillow, FFmpeg, 한국어 글꼴이 필요합니다. 이 의존성은 영상 재생이나 도구 사용에는 필요하지 않고 **영상 재생성에만** 쓰입니다.

```bash
python3 -m pip install Pillow
# FFmpeg는 운영체제의 패키지 관리자로 설치합니다.
python3 docs/media/render_intro.py
```

설명용 기본 글꼴은 macOS의 Pretendard ExtraBold·Regular이며 Apple SD Gothic Neo 또는 Linux의 Noto Sans CJK로 대체할 수 있습니다. 로고는 서체로 재조판하지 않고 원본 PNG를 사용합니다.
다른 환경에서는 한국어 글꼴 경로를 지정합니다. 글꼴 파일은 저장소에 포함하지 않습니다.

```bash
INTRO_FONT=/path/to/Regular.otf INTRO_FONT_BOLD=/path/to/Bold.otf python3 docs/media/render_intro.py
```

`brand-logo.png`는 제공된 원본 PNG와 체크섬이 같은 파일입니다. 투명 바깥 여백은 배치할 때만 제외합니다. `brand-tokens.json`에 원본에서 확인한 RGB 값과 화면용 파생색을 구분해 두었습니다.

`intro.json`의 문구를 고친 뒤 렌더링하면 MP4·GIF·포스터·스토리보드를 함께 갱신합니다.
`--stills`는 정지 이미지만, `--fps 24`는 다른 프레임률의 MP4를 만듭니다(그 경우 위 사양도 수정하세요).
내용이 바뀌면 이 대본과 README의 활용 예시도 함께 맞춥니다.

README에는 GIF를 이미지로 넣고 MP4 파일로 연결했습니다. 정지 이미지와 이 대본으로도 같은 내용을 확인할 수 있습니다.
