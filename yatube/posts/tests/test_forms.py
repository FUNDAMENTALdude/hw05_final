from django.test import TestCase, Client
from ..models import Post, Group
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='test title',
                                         description='test desctiption',
                                         slug='test-slug')
        cls.post = Post.objects.create(author=cls.user,
                                       text='text',
                                       group=cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_post_create_post(self):
        posts_count = Post.objects.count()

        form_data = {
            'text': 'text2',
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'auth'}))
        self.assertEqual(posts_count + 1, Post.objects.count())
        self.assertTrue(Post.objects.filter(text='text2').exists())
        self.assertEqual(response.status_code, 200)

    def test_post_edit_post(self):
        posts_count = Post.objects.count()

        form_data = {
            'text': 'text3',
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{PostFormTests.post.pk}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id':
                                             PostFormTests.post.pk}))
        self.assertEqual(posts_count, Post.objects.count())

        self.assertTrue(Post.objects.filter(text='text3').exists())
        self.assertEqual(response.status_code, 200)
