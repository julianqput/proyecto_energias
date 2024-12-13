function updateIcon() {
    const energyIcon = document.getElementById('energy-icon');
    
    const activeItem = document.querySelector('#energyCarousel .carousel-item.active');
    
    if (activeItem) {
        const iconClass = activeItem.getAttribute('data-icon');
        
        if (iconClass) {
            energyIcon.classList.remove('fas', 'fa-sun', 'fa-wind', 'fa-water');
            
            energyIcon.classList.add('fas', iconClass.split(' ')[1]);
        }
    }
}

document.getElementById('energyCarousel').addEventListener('slid.bs.carousel', updateIcon);

window.addEventListener('load', updateIcon);