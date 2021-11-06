from django.test import TestCase
from ..models import Group, Post
from django.contrib.auth import get_user_model

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='Тестовый заголовок',
                                         slug='Тестовый слаг',
                                         description='Тестовое описание')
        cls.post = Post.objects.create(author=cls.user,
                                       text='аб' * 10,)

    def test_models_have_correct_object_names(self):

        group = PostModelTest.group
        post = PostModelTest.post
        self.assertEqual(str(group),
                         group.title, 'Неверное __str__ в Group модели')
        self.assertEqual(str(post),
                         post.text[:15], 'Неверное __str__ в Post модели')

    def test_post_model_verbose_name(self):

        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата поста',
            'author': 'Автор',
            'group': 'Группа этого поста',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).verbose_name,
                                 expected_value)

    def test_post_model_help_text(self):

        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(post._meta.get_field(field).help_text,
                                 expected_value)
