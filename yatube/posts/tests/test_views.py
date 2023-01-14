import shutil

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User
from yatube.settings import (POSTS_NUMBER_PER_PAGE,
                             POSTS_FOR_SECOND_PAGE,
                             TEMP_MEDIA_ROOT)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UM')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.following = Follow.objects.create(
            user=cls.user,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адреса используют верные шаблоны."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Список постов в шаблоне index равен ожидаемому контексту."""
        response = self.authorized_client.get(reverse('posts:index'))
        expected = list(Post.objects.all()[:POSTS_NUMBER_PER_PAGE])
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def posts_compare(self, post, id, author, image, text, group):
        self.assertEqual(post.pk, id)
        self.assertEqual(post.author, author)
        self.assertEqual(post.text, text)
        self.assertEqual(post.group, group)
        self.assertEqual(post.image, image)

    def test_index_show_correct_context_first_object(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.posts_compare(
            first_object,
            self.post.pk,
            self.user,
            self.post.image,
            self.post.text,
            self.group)

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected = list(
            Post.objects.filter(group_id=self.group.id)[:POSTS_NUMBER_PER_PAGE]
        )
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_group_list_show_correct_context_first_object(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        first_object = response.context['page_obj'][0]
        self.posts_compare(
            first_object,
            self.post.pk,
            self.user,
            self.post.image,
            self.post.text,
            self.group)

    def test_profile_show_correct_context(self):
        """Список постов в шаблоне profile равен ожидаемому контексту."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        expected = list(
            Post.objects.filter(author_id=self.user.id)[:POSTS_NUMBER_PER_PAGE]
        )
        self.assertEqual(list(response.context.get('page_obj')), expected)

    def test_profile_show_correct_context_first_object(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        first_object = response.context['page_obj'][0]
        self.posts_compare(
            first_object,
            self.post.pk,
            self.user,
            self.post.image,
            self.post.text,
            self.group)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('one_post').text, self.post.text)
        self.assertEqual(response.context.get('one_post').author,
                         self.post.author)
        self.assertEqual(response.context.get('one_post').group,
                         self.post.group)
        self.assertEqual(response.context.get('one_post').image,
                         self.post.image)

    def test_create_post_edit_show_correct_context(self):
        """Шаблон create_post с post_edit сформирован
        с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        """Шаблон create_post с post_create сформирован
        с правильным контекстом."""
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

    def test_check_post_group_in_pages(self):
        """Созданный пост с выбранной группой отображается на страницах."""
        needed_pages = {
            reverse('posts:index'): Post.objects.get(group=self.post.group),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for page, test_post in needed_pages.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                page_with_posts = response.context.get('page_obj')
                self.assertIn(test_post, page_with_posts)

    def test_check_post_group_not_in_group(self):
        """Созданный пост не находится в группе,
        для которой не был предназначен."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        page_with_posts = response.context.get('page_obj')
        test_post = Post.objects.exclude(group=self.post.group)
        self.assertNotIn(test_post, page_with_posts)

    def test_cache(self):
        """"Корректность работы кеша для шаблона index."""
        post = Post.objects.create(
            text='Тестовый текст для кеширования',
            author=self.user,
            group=self.group,
        )
        response_1 = self.client.get(reverse('posts:index')).content
        post.delete()
        response_2 = self.client.get(reverse('posts:index')).content
        self.assertEqual(response_1, response_2)
        cache.clear()
        response_3 = self.client.get(reverse('posts:index')).content
        self.assertNotEqual(response_1, response_3)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='follower')
        cls.user_not_follower = User.objects.create_user(
            username='not_follower'
        )
        cls.user_following = User.objects.create_user(username='following')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_following,
        )

    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_not_follower = Client()
        self.client_auth_following = Client()
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_not_follower.force_login(self.user_not_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        """"Проверка возможности подписки авторизованного."""
        self.client_auth_follower.get(reverse(
            'posts:profile_follow', kwargs={
                'username': self.user_following
            })
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """"Проверка возможности отписки авторизованного."""
        self.client_auth_follower.get(reverse(
            'posts:profile_follow', kwargs={
                'username': self.user_following
            })
        )
        self.client_auth_follower.get(reverse(
            'posts:profile_unfollow', kwargs={
                'username': self.user_following
            })
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_new_post_exist_for_followers(self):
        """Проверка, что новый пост появляется в ленте у подписчика."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get(reverse('posts:follow_index'))
        post_text_0 = response.context['page_obj'][0].text
        self.assertEqual(post_text_0, self.post.text)

    def test_new_post_do_not_exist_for_not_followers(self):
        """Проверка, что новый пост не появляется в ленте у не подписчика."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_not_follower.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(response, self.post.text)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='UM')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group)
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_contain_posts(self):
        pages_posts = {
            reverse('posts:index'): POSTS_NUMBER_PER_PAGE,
            reverse('posts:index') + '?page=2': POSTS_FOR_SECOND_PAGE,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): POSTS_NUMBER_PER_PAGE,
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ) + '?page=2': POSTS_FOR_SECOND_PAGE,
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): POSTS_NUMBER_PER_PAGE,
            reverse('posts:profile',
                    kwargs={'username': self.user}
                    ) + '?page=2': POSTS_FOR_SECOND_PAGE,
        }
        for reverse_name, posts in pages_posts.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(len(response.context['page_obj']), posts)
