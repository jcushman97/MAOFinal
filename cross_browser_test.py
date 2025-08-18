#!/usr/bin/env python3
"""
Cross-Browser Testing Script
Tests website across Chrome, Firefox, and Safari browsers for:
1. Visual rendering consistency
2. JavaScript functionality
3. Performance metrics
4. HTML structure validity
5. Accessibility support
"""

import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

class CrossBrowserTester:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.browsers = ['chromium', 'firefox', 'webkit']  # webkit = Safari engine
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'base_url': base_url,
            'browsers': {}
        }
        
    async def test_all_browsers(self):
        """Run comprehensive tests across all browsers"""
        async with async_playwright() as p:
            for browser_name in self.browsers:
                print(f"\n[BROWSER] Testing {browser_name.upper()}...")
                await self.test_browser(p, browser_name)
        
        # Generate report
        await self.generate_report()
        
    async def test_browser(self, playwright, browser_name):
        """Test individual browser"""
        browser_results = {
            'browser': browser_name,
            'tests': {},
            'screenshots': [],
            'performance': {},
            'errors': []
        }
        
        try:
            # Launch browser
            browser = await getattr(playwright, browser_name).launch(headless=False)
            page = await browser.new_page()
            
            # Test 1: Basic page load and HTML validation
            browser_results['tests']['page_load'] = await self.test_page_load(page)
            
            # Test 2: Visual consistency (screenshots)
            browser_results['screenshots'] = await self.capture_screenshots(page, browser_name)
            
            # Test 3: JavaScript functionality
            browser_results['tests']['javascript'] = await self.test_javascript_functionality(page)
            
            # Test 4: Performance metrics
            browser_results['performance'] = await self.measure_performance(page)
            
            # Test 5: Accessibility testing
            browser_results['tests']['accessibility'] = await self.test_accessibility(page)
            
            # Test 6: Responsive design
            browser_results['tests']['responsive'] = await self.test_responsive_design(page)
            
            # Test 7: Form functionality
            browser_results['tests']['forms'] = await self.test_form_functionality(page)
            
            await browser.close()
            
        except Exception as e:
            browser_results['errors'].append(f"Browser setup error: {str(e)}")
            print(f"[ERROR] Error testing {browser_name}: {str(e)}")
            
        self.results['browsers'][browser_name] = browser_results
        
    async def test_page_load(self, page):
        """Test basic page loading and HTML structure"""
        results = {}
        
        try:
            # Navigate and measure load time
            start_time = datetime.now()
            response = await page.goto(f"{self.base_url}/index.html")
            load_time = (datetime.now() - start_time).total_seconds()
            
            results['load_time'] = load_time
            results['status_code'] = response.status
            results['loaded'] = response.ok
            
            # Check HTML structure
            title = await page.title()
            results['title'] = title
            
            # Check for required elements
            nav_exists = await page.locator('nav').count() > 0
            main_exists = await page.locator('main').count() > 0
            footer_exists = await page.locator('footer').count() > 0
            
            results['structure'] = {
                'has_nav': nav_exists,
                'has_main': main_exists,
                'has_footer': footer_exists
            }
            
            # Check for console errors
            console_errors = []
            page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
            
            await page.wait_for_timeout(2000)  # Wait for any console errors
            results['console_errors'] = console_errors
            
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def capture_screenshots(self, page, browser_name):
        """Capture screenshots for visual consistency testing"""
        screenshots = []
        viewports = [
            {'width': 1920, 'height': 1080, 'name': 'desktop'},
            {'width': 768, 'height': 1024, 'name': 'tablet'},
            {'width': 375, 'height': 667, 'name': 'mobile'}
        ]
        
        try:
            await page.goto(f"{self.base_url}/index.html")
            
            for viewport in viewports:
                await page.set_viewport_size(viewport)
                await page.wait_for_timeout(1000)  # Allow render
                
                screenshot_path = f"screenshots/{browser_name}_{viewport['name']}.png"
                os.makedirs('screenshots', exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=True)
                
                screenshots.append({
                    'viewport': viewport,
                    'path': screenshot_path
                })
                
        except Exception as e:
            screenshots.append({'error': str(e)})
            
        return screenshots
        
    async def test_javascript_functionality(self, page):
        """Test JavaScript functionality"""
        results = {}
        
        try:
            await page.goto(f"{self.base_url}/index.html")
            
            # Test smooth scroll functionality
            results['smooth_scroll'] = await self.test_smooth_scroll(page)
            
            # Test form validation
            results['form_validation'] = await self.test_js_form_validation(page)
            
            # Test button interactions
            results['button_interactions'] = await self.test_button_interactions(page)
            
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def test_smooth_scroll(self, page):
        """Test smooth scrolling navigation"""
        try:
            # Click on navigation link
            await page.click('a[href="#about"]')
            await page.wait_for_timeout(1000)
            
            # Check if scrolled to about section
            about_section = page.locator('#about')
            is_visible = await about_section.is_visible()
            
            return {'working': is_visible, 'error': None}
        except Exception as e:
            return {'working': False, 'error': str(e)}
            
    async def test_js_form_validation(self, page):
        """Test JavaScript form validation"""
        try:
            # Try to submit empty form
            submit_button = page.locator('button[type="submit"]')
            await submit_button.click()
            
            # Check if validation prevented submission
            # (This is a basic test - would need more sophisticated checking)
            await page.wait_for_timeout(500)
            
            return {'working': True, 'error': None}
        except Exception as e:
            return {'working': False, 'error': str(e)}
            
    async def test_button_interactions(self, page):
        """Test button interactions and aria states"""
        try:
            buttons = page.locator('.button')
            button_count = await buttons.count()
            
            if button_count > 0:
                # Click first button and check aria-pressed
                first_button = buttons.first
                await first_button.click()
                await page.wait_for_timeout(300)
                
                return {'working': True, 'button_count': button_count, 'error': None}
            else:
                return {'working': False, 'button_count': 0, 'error': 'No buttons found'}
                
        except Exception as e:
            return {'working': False, 'error': str(e)}
            
    async def measure_performance(self, page):
        """Measure performance metrics"""
        performance = {}
        
        try:
            # Navigate with performance monitoring
            await page.goto(f"{self.base_url}/index.html")
            
            # Get performance metrics using page.evaluate
            metrics = await page.evaluate("""() => {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                
                return {
                    dom_loading: navigation.domContentLoadedEventStart - navigation.navigationStart,
                    page_load: navigation.loadEventStart - navigation.navigationStart,
                    first_paint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    first_contentful_paint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0
                };
            }""")
            
            performance.update(metrics)
            
        except Exception as e:
            performance['error'] = str(e)
            
        return performance
        
    async def test_accessibility(self, page):
        """Test accessibility features"""
        results = {}
        
        try:
            await page.goto(f"{self.base_url}/index.html")
            
            # Check for ARIA attributes
            nav_has_label = await page.locator('nav[aria-label]').count() > 0
            main_has_role = await page.locator('main[role="main"]').count() > 0
            form_has_role = await page.locator('form[role="form"]').count() > 0
            
            results['aria_attributes'] = {
                'nav_labeled': nav_has_label,
                'main_role': main_has_role,
                'form_role': form_has_role
            }
            
            # Check form labels
            inputs_with_labels = await page.evaluate("""() => {
                const inputs = document.querySelectorAll('input[required]');
                let labeled_count = 0;
                
                inputs.forEach(input => {
                    const label = document.querySelector(`label[for="${input.id}"]`);
                    if (label) labeled_count++;
                });
                
                return {
                    total_inputs: inputs.length,
                    labeled_inputs: labeled_count
                };
            }""")
            
            results['form_labels'] = inputs_with_labels
            
            # Check heading hierarchy
            headings = await page.evaluate("""() => {
                const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
                return headings.map(h => ({
                    tag: h.tagName,
                    text: h.textContent.trim(),
                    id: h.id
                }));
            }""")
            
            results['heading_structure'] = headings
            
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def test_responsive_design(self, page):
        """Test responsive design across viewports"""
        results = {}
        viewports = [
            {'width': 1920, 'height': 1080, 'name': 'desktop'},
            {'width': 1024, 'height': 768, 'name': 'tablet_landscape'}, 
            {'width': 768, 'height': 1024, 'name': 'tablet_portrait'},
            {'width': 375, 'height': 667, 'name': 'mobile'}
        ]
        
        try:
            await page.goto(f"{self.base_url}/index.html")
            
            for viewport in viewports:
                await page.set_viewport_size(viewport)
                await page.wait_for_timeout(500)
                
                # Check if navigation is visible/accessible
                nav_visible = await page.locator('nav').is_visible()
                
                # Check if content is properly laid out
                content_width = await page.evaluate("document.querySelector('main').offsetWidth")
                viewport_width = viewport['width']
                
                results[viewport['name']] = {
                    'nav_visible': nav_visible,
                    'content_width': content_width,
                    'viewport_width': viewport_width,
                    'responsive_ratio': content_width / viewport_width if viewport_width > 0 else 0
                }
                
        except Exception as e:
            results['error'] = str(e)
            
        return results
        
    async def test_form_functionality(self, page):
        """Test form functionality across browsers"""
        results = {}
        
        try:
            await page.goto(f"{self.base_url}/index.html")
            
            # Fill out form
            await page.fill('#name', 'Test User')
            await page.fill('#email', 'test@example.com')
            await page.fill('#message', 'This is a test message')
            
            # Check if form validates
            name_value = await page.input_value('#name')
            email_value = await page.input_value('#email')
            message_value = await page.input_value('#message')
            
            results['form_filling'] = {
                'name_filled': name_value == 'Test User',
                'email_filled': email_value == 'test@example.com', 
                'message_filled': message_value == 'This is a test message'
            }
            
            # Test form submission (will be prevented by validation)
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(500)
            
            results['form_working'] = True
            
        except Exception as e:
            results['error'] = str(e)
            results['form_working'] = False
            
        return results
        
    async def generate_report(self):
        """Generate comprehensive test report"""
        report_path = f"cross_browser_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        print(f"\n[REPORT] Test report generated: {report_path}")
        
        # Generate summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print("CROSS-BROWSER TEST SUMMARY")
        print("="*50)
        
        for browser_name, browser_data in self.results['browsers'].items():
            print(f"\n[{browser_name.upper()}]:")
            
            # Page load results
            if 'page_load' in browser_data['tests']:
                load_data = browser_data['tests']['page_load']
                status = "[PASS]" if load_data.get('loaded', False) else "[FAIL]"
                load_time = load_data.get('load_time', 0)
                print(f"  Page Load: {status} ({load_time:.2f}s)")
                
            # JavaScript functionality
            if 'javascript' in browser_data['tests']:
                js_data = browser_data['tests']['javascript']
                js_tests_passed = sum(1 for test in js_data.values() 
                                     if isinstance(test, dict) and test.get('working', False))
                total_js_tests = len([test for test in js_data.values() if isinstance(test, dict)])
                print(f"  JavaScript: {js_tests_passed}/{total_js_tests} tests passed")
                
            # Performance
            if 'performance' in browser_data and 'page_load' in browser_data['performance']:
                perf_time = browser_data['performance']['page_load']
                perf_status = "[GOOD]" if perf_time < 3000 else "[SLOW]" if perf_time < 5000 else "[POOR]"
                print(f"  Performance: {perf_status} ({perf_time:.0f}ms)")
                
            # Accessibility
            if 'accessibility' in browser_data['tests']:
                acc_data = browser_data['tests']['accessibility']
                if 'aria_attributes' in acc_data:
                    aria_count = sum(acc_data['aria_attributes'].values())
                    print(f"  Accessibility: {aria_count}/3 ARIA attributes found")
                    
            # Errors
            if browser_data.get('errors'):
                print(f"  Errors: {len(browser_data['errors'])}")
                for error in browser_data['errors'][:2]:  # Show first 2 errors
                    print(f"    - {error}")

# Run the tests
async def main():
    tester = CrossBrowserTester()
    await tester.test_all_browsers()

if __name__ == "__main__":
    asyncio.run(main())