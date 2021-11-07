from django.test import TestCase, Client
from ..models import Post, Group
from django.contrib.auth import get_user_model
from django.urls import reverse

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

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
        small_img = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.png',
            content=small_img,
            content_type='image/gif'
        )
        form_data = {
            'text': 'text2',
            'image': uploaded
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:profile',
                                               kwargs={'username': 'auth'}))
        self.assertEqual(posts_count + 1, Post.objects.count())
        self.assertTrue(Post.objects.filter(text='text2',
                                            image='posts/small.png'
                                            ).exists())
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
