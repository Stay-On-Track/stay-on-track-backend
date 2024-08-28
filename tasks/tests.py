from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Task
from .serializers import TaskSerializer
from django.utils import timezone
import datetime

class TaskModelTests(TestCase):
    def test_task_creation(self):
        task = Task.objects.create(title="Test Task", description="This is a test task")
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.description, "This is a test task")
        self.assertFalse(task.completed)

    def test_task_str_method(self):
        task = Task.objects.create(title="Test Task")
        self.assertEqual(str(task), "Test Task")

    def test_auto_now_fields(self):
        task = Task.objects.create(title="Test Task")
        self.assertLess(timezone.now() - task.created_at, datetime.timedelta(seconds=1))
        self.assertLess(timezone.now() - task.updated_at, datetime.timedelta(seconds=1))

        # Test updated_at changes on update
        original_updated_at = task.updated_at
        task.title = "Updated Task"
        task.save()
        self.assertGreater(task.updated_at, original_updated_at)

    def test_blank_description(self):
        task = Task.objects.create(title="Test Task")
        self.assertEqual(task.description, "")

class TaskSerializerTests(TestCase):
    def test_task_serializer(self):
        task_data = {"title": "Test Task", "description": "This is a test task"}
        serializer = TaskSerializer(data=task_data)
        self.assertTrue(serializer.is_valid())

class TaskViewSetTests(APITestCase):
    def setUp(self):
        self.task = Task.objects.create(title="Test Task", description="This is a test task")
        self.url = reverse('task-list')

    # GET tests
    def test_get_task_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tasks = Task.objects.all()
        expected_data = TaskSerializer(tasks, many=True).data
        self.assertEqual(response.data, expected_data)

    def test_retrieve_task(self):
        url = reverse('task-detail', args=[self.task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = TaskSerializer(self.task).data
        self.assertEqual(response.data, expected_data)

    def test_retrieve_nonexistent_task(self):
        url = reverse('task-detail', args=[999])  # Assuming 999 is not a valid task ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # POST tests
    def test_create_task(self):
        data = {"title": "New Task", "description": "This is a new task"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Task.objects.filter(title="New Task").exists())
        for key, value in data.items():
            self.assertEqual(response.data[key], value)

    def test_create_task_invalid_data(self):
        data = {"title": "", "description": "This is an invalid task"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_missing_title(self):
        data = {"description": "This task is missing a title"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # PUT tests
    def test_update_task(self):
        url = reverse('task-detail', args=[self.task.id])
        data = {"title": "Updated Task", "description": "This task has been updated"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task.refresh_from_db()
        updated_task_data = TaskSerializer(self.task).data
        self.assertEqual(response.data, updated_task_data)

    def test_update_task_invalid_data(self):
        url = reverse('task-detail', args=[self.task.id])
        data = {"title": "", "description": "This is an invalid update"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # DELETE tests
    def test_delete_task(self):
        url = reverse('task-detail', args=[self.task.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.count(), 0)

    def test_delete_nonexistent_task(self):
        url = reverse('task-detail', args=[999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
