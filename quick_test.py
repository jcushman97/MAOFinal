#!/usr/bin/env python3
"""
Quick cross-browser test using file:// URLs
"""
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def test_file_based():
    # Get absolute path to index.html
    current_dir = os.getcwd()
    file_path = 'file:///' + current_dir.replace('\\', '/') + '/index.html'
    print(f'Testing file path: {file_path}')
    
    results = {}
    
    async with async_playwright() as p:
        for browser_name in ['chromium', 'firefox', 'webkit']:
            print(f'\n[BROWSER] Testing {browser_name.upper()}...')
            browser_results = {}
            
            try:
                browser = await getattr(p, browser_name).launch(headless=False)
                page = await browser.new_page()
                
                # Test basic page load
                start_time = datetime.now()
                response = await page.goto(file_path)
                load_time = (datetime.now() - start_time).total_seconds()
                
                browser_results['loaded'] = response.ok if response else True
                browser_results['load_time'] = load_time
                print(f'  Page loaded: {browser_results["loaded"]} ({load_time:.2f}s)')
                
                # Test title
                title = await page.title()
                browser_results['title'] = title
                print(f'  Title: {title}')
                
                # Check structure
                nav_count = await page.locator('nav').count()
                main_count = await page.locator('main').count()
                footer_count = await page.locator('footer').count()
                
                browser_results['structure'] = {
                    'nav': nav_count,
                    'main': main_count,
                    'footer': footer_count
                }
                print(f'  Structure: nav={nav_count}, main={main_count}, footer={footer_count}')
                
                # Test form elements
                name_input = await page.locator('#name').count()
                email_input = await page.locator('#email').count()
                message_input = await page.locator('#message').count()
                submit_button = await page.locator('button[type="submit"]').count()
                
                browser_results['form_elements'] = {
                    'name_input': name_input,
                    'email_input': email_input,
                    'message_input': message_input,
                    'submit_button': submit_button
                }
                print(f'  Form elements: name={name_input}, email={email_input}, message={message_input}, submit={submit_button}')
                
                # Test accessibility
                nav_aria = await page.locator('nav[aria-label]').count()
                main_role = await page.locator('main[role="main"]').count()
                form_role = await page.locator('form[role="form"]').count()
                
                browser_results['accessibility'] = {
                    'nav_aria': nav_aria,
                    'main_role': main_role,
                    'form_role': form_role
                }
                print(f'  Accessibility: nav_aria={nav_aria}, main_role={main_role}, form_role={form_role}')
                
                # Test responsive design at different viewports
                viewports = [
                    {'width': 1920, 'height': 1080, 'name': 'desktop'},
                    {'width': 768, 'height': 1024, 'name': 'tablet'},
                    {'width': 375, 'height': 667, 'name': 'mobile'}
                ]
                
                responsive_results = {}
                for viewport in viewports:
                    await page.set_viewport_size({'width': viewport['width'], 'height': viewport['height']})
                    await page.wait_for_timeout(500)
                    
                    # Take screenshot
                    screenshot_path = f'screenshots/{browser_name}_{viewport["name"]}_filetest.png'
                    os.makedirs('screenshots', exist_ok=True)
                    await page.screenshot(path=screenshot_path, full_page=True)
                    
                    # Check if nav is visible
                    nav_visible = await page.locator('nav').is_visible()
                    responsive_results[viewport['name']] = {
                        'nav_visible': nav_visible,
                        'screenshot': screenshot_path
                    }
                    
                print(f'  Screenshots taken for all viewports')
                browser_results['responsive'] = responsive_results
                
                # Test JavaScript functionality
                try:
                    # Test smooth scroll by clicking navigation link
                    await page.click('a[href="#about"]')
                    await page.wait_for_timeout(1000)
                    about_visible = await page.locator('#about').is_visible()
                    browser_results['smooth_scroll'] = about_visible
                    print(f'  Smooth scroll: {about_visible}')
                except Exception as js_error:
                    browser_results['smooth_scroll'] = False
                    print(f'  Smooth scroll: Failed - {str(js_error)}')
                
                # Test form filling
                try:
                    await page.fill('#name', 'Test User')
                    await page.fill('#email', 'test@example.com')
                    await page.fill('#message', 'Test message')
                    
                    name_value = await page.input_value('#name')
                    email_value = await page.input_value('#email')
                    message_value = await page.input_value('#message')
                    
                    browser_results['form_fill'] = {
                        'name_correct': name_value == 'Test User',
                        'email_correct': email_value == 'test@example.com',
                        'message_correct': message_value == 'Test message'
                    }
                    print(f'  Form filling: All fields working')
                except Exception as form_error:
                    browser_results['form_fill'] = {'error': str(form_error)}
                    print(f'  Form filling: Failed - {str(form_error)}')
                
                await browser.close()
                browser_results['status'] = 'success'
                
            except Exception as e:
                browser_results['status'] = 'error'
                browser_results['error'] = str(e)
                print(f'  Error: {str(e)}')
            
            results[browser_name] = browser_results
    
    # Print summary
    print('\n' + '='*60)
    print('CROSS-BROWSER TEST SUMMARY')
    print('='*60)
    
    for browser, data in results.items():
        print(f'\n[{browser.upper()}]:')
        if data.get('status') == 'success':
            print(f'  ✅ Page Load: {data.get("load_time", 0):.2f}s')
            print(f'  ✅ Title: {data.get("title", "N/A")}')
            structure = data.get('structure', {})
            print(f'  ✅ Structure: nav={structure.get("nav", 0)}, main={structure.get("main", 0)}, footer={structure.get("footer", 0)}')
            form = data.get('form_elements', {})
            print(f'  ✅ Form Elements: {sum(form.values())}/4 found')
            accessibility = data.get('accessibility', {})
            print(f'  ✅ Accessibility: {sum(accessibility.values())}/3 ARIA features')
            print(f'  ✅ Smooth Scroll: {data.get("smooth_scroll", False)}')
            form_fill = data.get('form_fill', {})
            if 'error' not in form_fill:
                fill_success = sum(1 for v in form_fill.values() if v)
                print(f'  ✅ Form Filling: {fill_success}/3 fields working')
            else:
                print(f'  ❌ Form Filling: Error')
        else:
            print(f'  ❌ Failed: {data.get("error", "Unknown error")}')
    
    return results

if __name__ == "__main__":
    asyncio.run(test_file_based())