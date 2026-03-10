from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=20, spacing=10, **kwargs)
        self.add_widget(Label(text="BR Converter (Android) — Em breve", font_size=22))
        self.add_widget(Label(text="Base Kivy pronta para reaproveitar o CORE.", font_size=14))
        self.add_widget(Button(text="Ok", size_hint=(1, None), height=48))

class BRConverterAndroid(App):
    def build(self):
        return Root()

if __name__ == "__main__":
    BRConverterAndroid().run()
