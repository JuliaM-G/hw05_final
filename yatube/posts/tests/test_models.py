from django.test import TestCase

from ..models import Group, Post, User
from yatube.settings import RETURN_SYMBOLS


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UM')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_group_verbose_name(self):
        """verbose_name в полях в Group совпадает с ожидаемым."""
        group = ModelTest.group
        field_verboses = {
            'title': 'Название',
            'slug': 'Адрес',
            'description': 'Описание',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_post_verbose_name(self):
        """verbose_name в полях в Post совпадает с ожидаемым."""
        post = ModelTest.post
        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
            'image': 'Картинка',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_post_help_text(self):
        """help_text в полях в Post совпадает с ожидаемым."""
        post = ModelTest.post
        field_help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост',
            'image': 'Картинка к Вашему посту',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_post_name_is_text_field(self):
        """В поле __str__  объекта post
        записано значение поля post.text[:15]."""
        post = ModelTest.post
        expected_object_name = post.text[:RETURN_SYMBOLS]
        self.assertEqual(expected_object_name, str(post))

    def test_group_name_is_title_field(self):
        """В поле __str__  объекта group записано значение поля group.title."""
        group = ModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
