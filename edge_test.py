#!/usr/bin/env python3
"""
Edge Browser Test using Playwright
"""
import asyncio
import os
from datetime import datetime
from playwright.async_api import async_playwright

async def test_edge_browser():
    # Get absolute path to index.html
    current_dir = os.getcwd()
    file_path = 'file:///' + current_dir.replace('\\', '/') + '/index.html'
    print(f'Testing file path: {file_path}')
    
    try:
        async with async_playwright() as p:
            print('\n[BROWSER] Testing EDGE (Chromium-based)...')
            
            # Use chromium engine which is what Edge uses
            browser = await p.chromium.launch(
                headless=False,
                channel='msedge'  # Use Microsoft Edge if available
            )
            page = await browser.new_page()
            
            # Test basic page load
            start_time = datetime.now()
            response = await page.goto(file_path)
            load_time = (datetime.now() - start_time).total_seconds()
            
            print(f'  Page loaded: {response.ok if response else True} ({load_time:.2f}s)')
            
            # Test title
            title = await page.title()
            print(f'  Title: {title}')
            
            # Check structure
            nav_count = await page.locator('nav').count()
            main_count = await page.locator('main').count()
            footer_count = await page.locator('footer').count()
            print(f'  Structure: nav={nav_count}, main={main_count}, footer={footer_count}')
            
            # Test form elements
            name_input = await page.locator('#name').count()
            email_input = await page.locator('#email').count()
            message_input = await page.locator('#message').count()
            submit_button = await page.locator('button[type="submit"]').count()
            print(f'  Form elements: name={name_input}, email={email_input}, message={message_input}, submit={submit_button}')
            
            # Test CSS Grid support
            grid_support = await page.evaluate("""
                () => {
                    return CSS.supports('display', 'grid');
                }
            """)
            print(f'  CSS Grid support: {grid_support}')
            
            # Test CSS Custom Properties support
            custom_props_support = await page.evaluate("""
                () => {
                    return CSS.supports('--custom', 'value');
                }
            """)
            print(f'  CSS Custom Properties support: {custom_props_support}')
            
            # Test JavaScript features
            es6_support = await page.evaluate("""
                () => {
                    try {
                        eval('const arrow = () => {};');
                        return true;
                    } catch (e) {
                        return false;
                    }
                }
            """)
            print(f'  ES6 Arrow Functions support: {es6_support}')
            
            # Take screenshots at different viewports
            viewports = [
                {'width': 1920, 'height': 1080, 'name': 'desktop'},
                {'width': 768, 'height': 1024, 'name': 'tablet'},
                {'width': 375, 'height': 667, 'name': 'mobile'}
            ]
            
            for viewport in viewports:
                await page.set_viewport_size({'width': viewport['width'], 'height': viewport['height']})
                await page.wait_for_timeout(500)
                
                screenshot_path = f'screenshots/edge_{viewport["name"]}.png'
                os.makedirs('screenshots', exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f'  Screenshot saved: {screenshot_path}')
            
            # Test smooth scroll
            try:
                await page.click('a[href="#about"]')
                await page.wait_for_timeout(1000)
                about_visible = await page.locator('#about').is_visible()
                print(f'  Smooth scroll: {about_visible}')
            except Exception as e:
                print(f'  Smooth scroll: Failed - {str(e)}')
            
            # Test form filling
            try:
                await page.fill('#name', 'Edge Test User')
                await page.fill('#email', 'edge@test.com')
                await page.fill('#message', 'Testing in Edge browser')
                
                name_value = await page.input_value('#name')
                email_value = await page.input_value('#email')
                message_value = await page.input_value('#message')
                
                form_success = (name_value == 'Edge Test User' and 
                              email_value == 'edge@test.com' and 
                              message_value == 'Testing in Edge browser')
                print(f'  Form filling: {form_success}')
            except Exception as e:
                print(f'  Form filling: Failed - {str(e)}')
            
            await browser.close()
            print('  Edge test completed successfully')
            
    except Exception as e:
        print(f'  Edge test failed: {str(e)}')
        print('  Note: Edge browser may not be available or properly configured')

if __name__ == "__main__":
    asyncio.run(test_edge_browser())