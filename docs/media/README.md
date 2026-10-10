# policy-research-kit 소개영상

30초 한국어 사용 예시. 로고는 1920px 화면에서 너비 144px로 줄이고, 실제 사용하는 터미널·요청·결과 파일에 화면을 배분했습니다.

Claude Code의 요청·응답과 결과 파일을 재구성한 30초 사용 예시입니다. 가상 과제이며 실제 실행 녹화는 아닙니다.

화면 속 응답·파일 내용은 사용법 설명을 위한 작성 예시입니다. Claude Code를 실행해 얻은 산출물이나 성능 측정 결과로 제시하지 않습니다. 터미널·파일 뷰어의 배치는 가독성을 위해 편집했으며 실제 제품의 별도 GUI가 아닙니다.

## 영상 구성

| 구간 | 화면 | 읽을 내용 |
|---|---|---|
| 0–7초 | 주제와 자료를 주고, 목차부터 확인합니다 | 먼저 연구 범위와 목차를 조정한 뒤 조사·집필을 시작합니다. |
| 7–14초 | 목차를 보고, 조사 방향을 바꿀 수 있습니다 | “3장에 해외사례를 추가해줘”처럼 바로 수정 요청을 합니다. |
| 14–23초 | 초안의 주장과 근거를 따로 대조합니다 | 근거가 부족한 문장은 위치·문제·수정 방향을 기록합니다. |
| 23–30초 | 초안과 함께, 근거·검수 기록이 남습니다 | 나중에 “이 판단의 근거가 무엇인가”를 파일에서 다시 확인합니다. |

## 파일·근거

- [MP4](intro.mp4): 1920×1080, 30fps, 30초, 무음 H.264
- [README GIF](intro-preview.gif): 같은 30초 전체, 960×540, 8fps
- [포스터](intro-poster.png) · [4개 장면](intro-storyboard.png)
- [대본·화면 데이터](intro.json) · [렌더러](render_intro.py)

기준 소스 커밋: `f1366e5a2595530a9da1fa33de3a8973bb814e6a`. 영상 길이는 실제 처리시간을 뜻하지 않습니다.

- [skills/rnd-policy-research-orchestrator/SKILL.md](../../skills/rnd-policy-research-orchestrator/SKILL.md)
- [agents/policy-report-reviewer.md](../../agents/policy-report-reviewer.md)
- [agents/policy-research-investigator.md](../../agents/policy-research-investigator.md)

## 다시 만들기

Python 3.9+, Pillow, FFmpeg, 한국어 글꼴이 필요합니다. 이 의존성은 영상 재생성에만 쓰입니다.

```bash
python3 -m pip install Pillow
python3 docs/media/render_intro.py
# 정지 이미지 먼저 확인
python3 docs/media/render_intro.py --stills
```

기본 글꼴은 Pretendard이며 Apple SD Gothic Neo 또는 Noto Sans CJK를 대체로 사용합니다. `INTRO_FONT`, `INTRO_FONT_BOLD` 환경변수로 글꼴 경로를 지정할 수 있습니다. `intro.json`의 화면 문구를 바꾼 뒤 다시 렌더링하면 MP4·GIF·포스터·스토리보드를 갱신합니다. 원본 로고 PNG는 수정하지 않으며 렌더링 전에 체크섬을 확인합니다.
