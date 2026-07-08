import sys

from ui.app import App


def main() -> int:
    app = App()
    app.update()
    app.after(200, app.destroy)
    app.mainloop()
    print("OK: ventana principal construida y cerrada sin errores")
    return 0


if __name__ == "__main__":
    sys.exit(main())
