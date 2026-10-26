import sys
from types import SimpleNamespace

from app import ask as ask_module


def test_main_keeps_follow_up_questions_in_the_same_chat(monkeypatch, capsys):
    class FakeChat:
        def __init__(self):
            self.questions = []

        def send_message(self, question):
            self.questions.append(question)
            return SimpleNamespace(
                text=f"answer: {question}",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=12,
                    candidates_token_count=8,
                ),
            )

    class FakeChats:
        def __init__(self, chat):
            self.chat = chat
            self.created = 0

        def create(self, model):
            self.created += 1
            return self.chat

    chat = FakeChat()
    chats = FakeChats(chat)
    monkeypatch.setattr(ask_module.genai, "Client", lambda **kwargs: SimpleNamespace(chats=chats))
    monkeypatch.setattr(sys, "argv", ["app.ask", "最初の質問"])
    answers = iter(["続きの質問", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    ask_module.main()

    assert chats.created == 1
    assert chat.questions == ["最初の質問", "続きの質問"]
    output = capsys.readouterr().out
    assert "answer: 続きの質問" in output
    assert output.count("[トークン数] 入力: 12 / 出力: 8") == 2


def test_ask_displays_unknown_counts_when_usage_metadata_is_missing(capsys):
    class FakeChat:
        def send_message(self, question):
            return SimpleNamespace(text="answer", usage_metadata=None)

    assert ask_module.ask("質問", FakeChat()) == "answer"

    assert "[トークン数] 入力: 不明 / 出力: 不明" in capsys.readouterr().out