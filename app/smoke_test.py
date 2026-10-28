from app.llm import get_llm


def main() -> None:
    llm = get_llm()
    print(llm.invoke("Say hello in one line").content)


if __name__ == "__main__":
    main()