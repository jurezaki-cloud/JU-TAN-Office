import flet as ft

def main(page: ft.Page):
    page.title = "JU-TAN Office"
    page.window.width = 1280
    page.window.height = 800

    page.add(
        ft.Text(
            "Dobrodošel v JU-TAN Office",
            size=32,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Text(
            "Prva različica poslovnega sistema.",
            size=18,
        ),
        ft.ElevatedButton("Nov račun")
    )

ft.app(target=main)