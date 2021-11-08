from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.client import Client
from django.urls import reverse
from ..models import Post, Group, Comment, Follow
from django import forms

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


User = get_user_model()


class PostViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.jpeg',
            content=small_img,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        # 3-й пользователь нужен для теста подписок
        cls.user3 = User.objects.create_user(username='auth3')
        cls.group = Group.objects.create(title='test title',
                                         description='test desctiption',
                                         slug='test-slug')
        cls.post = Post.objects.create(author=cls.user,
                                       text='text',
                                       group=cls.group,
                                       image='posts/small.jpeg')
        # Посты с группой и пользователем
        for i in range(11):
            Post.objects.create(author=cls.user,
                                text='text0',
                                group=cls.group,
                                image='posts/small.jpeg')
        # Пост от user3
        Post.objects.create(author=cls.user3,
                            text='text3',
                            )
        # Пост без группы
        Post.objects.create(author=cls.user,
                            text='text1',
                            image='posts/small.jpeg')
        # Пост от другого пользователя и без группы

        Post.objects.create(author=cls.user2,
                            text='text2',
                            image='posts/small.jpeg'
                            )
        cls.comment1 = Comment.objects.create(text='com1',
                                              post=cls.post, author=cls.user)
        cls.comment2 = Comment.objects.create(text='com2',
                                              post=cls.post, author=cls.user2)
        # Пусть авторизованный клиент user будет подписан на user2 и user3
        Follow.objects.create(user=cls.user, author=cls.user2)
        Follow.objects.create(user=cls.user, author=cls.user3)
        # user2 подписан только на пользователя user3
        Follow.objects.create(user=cls.user2, author=cls.user3)

    def setUp(self):
        self.authorized_client2 = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTest.user)
        self.authorized_client2.force_login(PostViewsTest.user2)

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

    def test_index_second_page_contains_five_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

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
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_edit',
                                                      kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    # Также проверяется контекст с комментариями

    def test_post_detail_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id': '1'}))

        comment = response.context['comments'][1]
        comment_text = comment.text
        comment_auth = comment.author
        comment_post = comment.post

        self.assertEqual(response.context.get('post').text, 'text')
        self.assertEqual(response.context.get('post').author,
                         PostViewsTest.user)
        self.assertEqual(response.context.get('post').group,
                         PostViewsTest.group)
        self.assertEqual(response.context.get('post').image,
                         'posts/small.jpeg')

        self.assertEqual(response.context['comments'].count(), 2)

        self.assertEqual(comment_text, 'com2')
        self.assertEqual(comment_post, PostViewsTest.post)
        self.assertEqual(comment_auth, PostViewsTest.user2)

    def test_index_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][1]
        post_text_1 = first_obj.text
        post_user_1 = first_obj.author
        post_image_1 = first_obj.image
        self.assertEqual(post_user_1, PostViewsTest.user)
        self.assertEqual(post_text_1, 'text1')
        self.assertEqual(post_image_1, 'posts/small.jpeg')

    def test_group_posts_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:group_posts',
                                                      kwargs={'slug':
                                                              'test-slug'}))
        first_obj = response.context['page_obj'][3]
        post_text_3 = first_obj.text
        post_group_3 = first_obj.group
        post_user_3 = first_obj.author
        post_image_3 = first_obj.image
        self.assertEqual(post_text_3, 'text0')
        self.assertEqual(post_user_3, PostViewsTest.user)
        self.assertEqual(post_group_3, PostViewsTest.group)
        self.assertEqual(post_image_3, 'posts/small.jpeg')

    def test_profile_pages_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:profile',
                                                      kwargs={'username':
                                                              'auth2'}))
        user = User.objects.get(username='auth2')
        first_obj = response.context['page_obj'][0]
        post_text_0 = first_obj.text
        post_user_0 = first_obj.author
        post_image_0 = first_obj.image
        self.assertEqual(post_text_0, 'text2')
        self.assertEqual(post_user_0, user)
        self.assertEqual(post_image_0, 'posts/small.jpeg')

    # В результате 1го теста должно выдать количество записей от user2 и user3
    # В результате 2го теста выдать количество записей(1) от user3
    def test_follow_index_first_page_contains_two_records(self):
        response1 = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response1.context['page_obj']), 2)
        response2 = self.authorized_client2.get(reverse('posts:follow_index'))
        self.assertEqual(len(response2.context['page_obj']), 1)

    # Проверяем количество подписок после подписки и отписки
    def test_follow_working(self):
        self.authorized_client2.get(reverse('posts:'
                                            'profile_follow',
                                            kwargs={'username': 'auth'}))
        follow2 = Follow.objects.filter(user=PostViewsTest.user2)
        self.assertEqual(len(follow2), 2)

    def test_unfollow_worling(self):
        self.authorized_client2.get(reverse('posts:'
                                            'profile_unfollow',
                                            kwargs={'username': 'auth'}))
        follow1 = Follow.objects.filter(user=PostViewsTest.user2)
        self.assertEqual(len(follow1), 1)
