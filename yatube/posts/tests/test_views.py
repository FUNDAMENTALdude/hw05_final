from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse
from ..models import Post, Group
from django import forms


User = get_user_model()


class PostViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(title='test title',
                                         description='test desctiption',
                                         slug='test-slug')
        cls.post = Post.objects.create(author=cls.user,
                                       text='text',
                                       group=cls.group)
        # Посты с группой и пользователем
        for i in range(11):
            Post.objects.create(author=cls.user,
                                text='text0',
                                group=cls.group)
        # Пост без группы
        Post.objects.create(author=cls.user,
                            text='text1',)
        # Пост от другого пользователя и без группы

        Post.objects.create(author=cls.user2,
                            text='text2',
                            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.user)

    # Проверки шаблонов
    def test_pages_uses_correct_templates(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts',
                    kwargs={'slug': 'test-slug'}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'auth'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'}): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    # Проверки паджинации
    def test_index_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_four_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 4)

    def test_group_posts_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug': 'test-slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_posts_second_page_contains_two_records(self):
        response = self.client.get(reverse('posts:group_posts',
                                           kwargs={'slug':
                                                   'test-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_profile_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'auth'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_three_records(self):
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username':
                                                   'auth'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    # Проверка контекста

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_post_detail_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id': '1'}))
        self.assertEqual(response.context.get('post').text, 'text')
        self.assertEqual(response.context.get('post').author,
                         PostViewsTest.user)
        self.assertEqual(response.context.get('post').group,
                         PostViewsTest.group)

    def test_index_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][1]
        post_text_1 = first_obj.text
        post_user_1 = first_obj.author
        self.assertEqual(post_user_1, PostViewsTest.user)
        self.assertEqual(post_text_1, 'text1')

    def test_group_posts_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_posts',
                                                      kwargs={'slug':
                                                              'test-slug'}))
        first_obj = response.context['page_obj'][3]
        post_text_3 = first_obj.text
        post_group_3 = first_obj.group
        post_user_3 = first_obj.author
        self.assertEqual(post_text_3, 'text0')
        self.assertEqual(post_user_3, PostViewsTest.user)
        self.assertEqual(post_group_3, PostViewsTest.group)

    def test_profile_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:profile',
                                                      kwargs={'username':
                                                              'auth2'}))
        user = User.objects.get(username='auth2')
        first_obj = response.context['page_obj'][0]
        post_text_0 = first_obj.text
        post_user_0 = first_obj.author
        self.assertEqual(post_text_0, 'text2')
        self.assertEqual(post_user_0, user)
