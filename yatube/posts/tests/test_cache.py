from django.test import TestCase, Client
from ..models import Post, Group
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache

User = get_user_model()


class ChacheTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(title='test title',
                                         description='test desctiption',
                                         slug='test-slug')
        cls.post = Post.objects.create(author=ChacheTests.user,
                                       text='text',
                                       group=ChacheTests.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(ChacheTests.user)

    def test_cache_index_page(self):
        response1 = self.authorized_client.get(reverse('posts:index'))
        content1 = response1.content
        post = ChacheTests.post
        post.delete()
        response2 = self.authorized_client.get(reverse('posts:index'))
        content2 = response2.content
        self.assertEqual(content1, content2)
        cache.clear()
        response3 = self.authorized_client.get(reverse('posts:index'))
        content3 = response3.content
        self.assertNotEqual(content3, content2)
