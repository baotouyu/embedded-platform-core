import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_rtthread_osal_thread_join_waits_for_entry_completion(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_osal_thread_smoke.c"
    executable = tmp_path / "rtthread_osal_thread_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_thread.h"

            extern int fake_thread_create_count;
            extern int fake_thread_startup_count;
            extern int fake_thread_delete_count;
            extern int fake_thread_entry_ran;
            extern int fake_thread_startup_should_fail;
            extern int fake_self_is_created_thread;
            extern unsigned int fake_thread_stack_size;
            extern unsigned int fake_thread_priority;
            extern unsigned int fake_thread_tick;
            extern unsigned int fake_sem_create_initial;
            extern int fake_sem_take_count;
            extern int fake_sem_delete_count;
            extern int fake_active_allocations;

            static void *worker_entry(void *arg)
            {
                int *value = (int *)arg;

                *value += 1;
                return (void *)0x1234;
            }

            int main(void)
            {
                ep_thread_t *thread = 0;
                int value = 41;

                if (ep_thread_create(0, "bad", worker_entry, &value) == EP_OK) {
                    return 1;
                }

                if (ep_thread_create(&thread, "bad", 0, &value) == EP_OK) {
                    return 2;
                }

                if (ep_thread_join(0) == EP_OK) {
                    return 3;
                }

                if (ep_thread_create(&thread, "ep-worker", worker_entry, &value) != EP_OK) {
                    return 4;
                }

                if (thread == 0) {
                    return 5;
                }

                if (fake_thread_create_count != 1 || fake_thread_startup_count != 1) {
                    return 6;
                }

                if (fake_thread_stack_size != 4096u || fake_thread_priority != 20u || fake_thread_tick != 10u) {
                    return 7;
                }

                if (fake_sem_create_initial != 0u) {
                    return 8;
                }

                if (fake_thread_entry_ran != 1 || value != 42) {
                    return 9;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 10;
                }

                if (fake_sem_take_count != 1 || fake_sem_delete_count != 1) {
                    return 11;
                }

                if (fake_active_allocations != 0) {
                    return 12;
                }

                fake_thread_startup_should_fail = 1;
                if (ep_thread_create(&thread, "startup-fail", worker_entry, &value) != EP_ERR_UNSUPPORTED) {
                    return 13;
                }

                if (fake_thread_delete_count != 1 || fake_sem_delete_count != 2) {
                    return 14;
                }

                if (fake_active_allocations != 0) {
                    return 15;
                }

                fake_thread_startup_should_fail = 0;
                if (ep_thread_create(&thread, "self-join", worker_entry, &value) != EP_OK) {
                    return 16;
                }

                fake_self_is_created_thread = 1;
                if (ep_thread_join(thread) != EP_ERR_INVAL) {
                    return 17;
                }

                if (fake_sem_take_count != 1 || fake_sem_delete_count != 2) {
                    return 18;
                }

                fake_self_is_created_thread = 0;
                if (ep_thread_join(thread) != EP_OK) {
                    return 19;
                }

                if (fake_sem_take_count != 2 || fake_sem_delete_count != 3) {
                    return 20;
                }

                if (fake_active_allocations != 0) {
                    return 21;
                }

                return 0;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_include = tmp_path / "rtthread.h"
    rtthread_include.write_text(
        textwrap.dedent(
            """
            #ifndef RTTHREAD_H
            #define RTTHREAD_H

            #include <stddef.h>
            #include <stdint.h>

            typedef int rt_err_t;
            typedef int rt_int32_t;
            typedef size_t rt_size_t;
            typedef unsigned int rt_uint32_t;
            typedef unsigned int rt_uint8_t;

            #define RT_EOK 0
            #define RT_ETIMEOUT 2
            #define RT_EFULL 3
            #define RT_ENOMEM 4
            #define RT_NULL ((void *)0)
            #define RT_IPC_FLAG_FIFO 0
            #define RT_WAITING_NO 0
            #define RT_WAITING_FOREVER (-1)

            typedef struct fake_thread *rt_thread_t;
            typedef struct fake_mutex *rt_mutex_t;
            typedef struct fake_mq *rt_mq_t;
            typedef struct fake_sem *rt_sem_t;

            void *rt_malloc(rt_size_t size);
            void rt_free(void *ptr);
            uint64_t rt_tick_get_millisecond(void);
            rt_err_t rt_thread_mdelay(rt_int32_t timeout_ms);
            rt_int32_t rt_tick_from_millisecond(rt_int32_t timeout_ms);
            rt_thread_t rt_thread_create(const char *name, void (*entry)(void *), void *parameter, rt_uint32_t stack_size, rt_uint8_t priority, rt_uint32_t tick);
            rt_err_t rt_thread_startup(rt_thread_t thread);
            rt_err_t rt_thread_delete(rt_thread_t thread);
            rt_thread_t rt_thread_self(void);
            rt_mutex_t rt_mutex_create(const char *name, rt_uint32_t flag);
            rt_err_t rt_mutex_take(rt_mutex_t mutex, rt_int32_t timeout);
            rt_err_t rt_mutex_release(rt_mutex_t mutex);
            rt_mq_t rt_mq_create(const char *name, rt_size_t item_size, rt_size_t max_msgs, rt_uint32_t flag);
            rt_err_t rt_mq_send(rt_mq_t mq, const void *buffer, rt_size_t size);
            rt_err_t rt_mq_send_wait(rt_mq_t mq, const void *buffer, rt_size_t size, rt_int32_t timeout);
            rt_err_t rt_mq_recv(rt_mq_t mq, void *buffer, rt_size_t size, rt_int32_t timeout);
            rt_sem_t rt_sem_create(const char *name, rt_uint32_t value, rt_uint32_t flag);
            rt_err_t rt_sem_take(rt_sem_t sem, rt_int32_t timeout);
            rt_err_t rt_sem_release(rt_sem_t sem);
            rt_err_t rt_sem_delete(rt_sem_t sem);

            #endif
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_fake = tmp_path / "fake_rtthread.c"
    rtthread_fake.write_text(
        textwrap.dedent(
            """
            #include "rtthread.h"

            #include <stdlib.h>

            struct fake_thread {
                void (*entry)(void *);
                void *parameter;
            };

            struct fake_mutex { int unused; };
            struct fake_mq { int unused; };
            struct fake_sem { unsigned int count; };

            int fake_thread_create_count;
            int fake_thread_startup_count;
            int fake_thread_delete_count;
            int fake_thread_entry_ran;
            int fake_thread_startup_should_fail;
            int fake_self_is_created_thread;
            static rt_thread_t fake_last_created_thread;
            unsigned int fake_thread_stack_size;
            unsigned int fake_thread_priority;
            unsigned int fake_thread_tick;
            unsigned int fake_sem_create_initial = 999u;
            int fake_sem_take_count;
            int fake_sem_delete_count;
            int fake_active_allocations;

            void *rt_malloc(rt_size_t size)
            {
                void *ptr = malloc(size);
                if (ptr != 0) {
                    ++fake_active_allocations;
                }
                return ptr;
            }

            void rt_free(void *ptr)
            {
                if (ptr != 0) {
                    --fake_active_allocations;
                }
                free(ptr);
            }

            uint64_t rt_tick_get_millisecond(void)
            {
                return 0;
            }

            rt_err_t rt_thread_mdelay(rt_int32_t timeout_ms)
            {
                (void)timeout_ms;
                return RT_EOK;
            }

            rt_int32_t rt_tick_from_millisecond(rt_int32_t timeout_ms)
            {
                return timeout_ms;
            }

            rt_thread_t rt_thread_create(const char *name,
                                         void (*entry)(void *),
                                         void *parameter,
                                         rt_uint32_t stack_size,
                                         rt_uint8_t priority,
                                         rt_uint32_t tick)
            {
                struct fake_thread *thread;

                (void)name;

                thread = (struct fake_thread *)malloc(sizeof(*thread));
                if (thread == 0) {
                    return RT_NULL;
                }

                thread->entry = entry;
                thread->parameter = parameter;
                fake_thread_stack_size = stack_size;
                fake_thread_priority = priority;
                fake_thread_tick = tick;
                fake_last_created_thread = thread;
                ++fake_thread_create_count;
                return thread;
            }

            rt_err_t rt_thread_startup(rt_thread_t thread)
            {
                ++fake_thread_startup_count;
                if (thread == RT_NULL || thread->entry == 0) {
                    return -RT_ETIMEOUT;
                }

                if (fake_thread_startup_should_fail) {
                    return -RT_ETIMEOUT;
                }

                thread->entry(thread->parameter);
                ++fake_thread_entry_ran;
                free(thread);
                return RT_EOK;
            }

            rt_err_t rt_thread_delete(rt_thread_t thread)
            {
                if (thread == RT_NULL) {
                    return -RT_ETIMEOUT;
                }

                ++fake_thread_delete_count;
                free(thread);
                return RT_EOK;
            }

            rt_thread_t rt_thread_self(void)
            {
                return fake_self_is_created_thread ? fake_last_created_thread : RT_NULL;
            }

            rt_mutex_t rt_mutex_create(const char *name, rt_uint32_t flag)
            {
                (void)name;
                (void)flag;
                return (rt_mutex_t)1;
            }

            rt_err_t rt_mutex_take(rt_mutex_t mutex, rt_int32_t timeout)
            {
                (void)mutex;
                (void)timeout;
                return RT_EOK;
            }

            rt_err_t rt_mutex_release(rt_mutex_t mutex)
            {
                (void)mutex;
                return RT_EOK;
            }

            rt_mq_t rt_mq_create(const char *name, rt_size_t item_size, rt_size_t max_msgs, rt_uint32_t flag)
            {
                (void)name;
                (void)item_size;
                (void)max_msgs;
                (void)flag;
                return (rt_mq_t)1;
            }

            rt_err_t rt_mq_send(rt_mq_t mq, const void *buffer, rt_size_t size)
            {
                (void)mq;
                (void)buffer;
                (void)size;
                return RT_EOK;
            }

            rt_err_t rt_mq_send_wait(rt_mq_t mq, const void *buffer, rt_size_t size, rt_int32_t timeout)
            {
                (void)mq;
                (void)buffer;
                (void)size;
                (void)timeout;
                return RT_EOK;
            }

            rt_err_t rt_mq_recv(rt_mq_t mq, void *buffer, rt_size_t size, rt_int32_t timeout)
            {
                (void)mq;
                (void)buffer;
                (void)size;
                (void)timeout;
                return RT_EOK;
            }

            rt_sem_t rt_sem_create(const char *name, rt_uint32_t value, rt_uint32_t flag)
            {
                struct fake_sem *sem;

                (void)name;
                (void)flag;

                sem = (struct fake_sem *)malloc(sizeof(*sem));
                if (sem == 0) {
                    return RT_NULL;
                }

                sem->count = value;
                fake_sem_create_initial = value;
                return sem;
            }

            rt_err_t rt_sem_take(rt_sem_t sem, rt_int32_t timeout)
            {
                (void)timeout;

                if (sem == RT_NULL || sem->count == 0u) {
                    return -RT_ETIMEOUT;
                }

                --sem->count;
                ++fake_sem_take_count;
                return RT_EOK;
            }

            rt_err_t rt_sem_release(rt_sem_t sem)
            {
                if (sem == RT_NULL) {
                    return -RT_ETIMEOUT;
                }

                ++sem->count;
                return RT_EOK;
            }

            rt_err_t rt_sem_delete(rt_sem_t sem)
            {
                if (sem == RT_NULL) {
                    return -RT_ETIMEOUT;
                }

                ++fake_sem_delete_count;
                free(sem);
                return RT_EOK;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(tmp_path),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(rtthread_fake),
            str(REPO_ROOT / "platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run_result.returncode == 0, (
        f"run failed\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
